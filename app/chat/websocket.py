from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.db.session import get_db
from app.models.message import Message
from app.auth.jwt_handler import decode_token
from app.core.rate_limiter import is_rate_limited
from datetime import datetime
import uuid
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# { "user-uuid-string": WebSocket }
connections: dict = {}


async def broadcast_online_status(user_id: str, online: bool):
    payload = json.dumps({
        "type":    "online_status",
        "user_id": user_id,
        "online":  online
    })
    for uid, sock in list(connections.items()):
        if uid != user_id:
            try:
                await sock.send_text(payload)
            except Exception:
                connections.pop(uid, None)


async def get_group_member_ids(db: Session, conversation_id: str, exclude_user_id: str) -> list:
    rows = db.execute(sql_text(
        "SELECT user_id FROM group_members WHERE conversation_id = :cid"
    ), {"cid": conversation_id}).fetchall()
    return [str(r[0]) for r in rows if str(r[0]) != exclude_user_id]


async def is_group_conversation(db: Session, conversation_id: str) -> bool:
    row = db.execute(sql_text(
        "SELECT is_group FROM conversations WHERE id = :id"
    ), {"id": conversation_id}).fetchone()
    return bool(row and row[0])


@router.websocket("/chat/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):

    # ── Auth ──────────────────────────────────────────────────────────────────
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return

    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001)
        return

    if payload.get("user_id") != user_id:
        await websocket.close(code=4001)
        return

    await websocket.accept()

    if user_id in connections:
        try:
            await connections[user_id].close()
        except Exception:
            pass
    connections[user_id] = websocket
    logger.debug(f"[WS] {user_id} connected. Online: {len(connections)}")

    await broadcast_online_status(user_id, True)

    await websocket.send_text(json.dumps({
        "type":         "online_list",
        "online_users": list(connections.keys())
    }))

    db: Session = next(get_db())

    # ── Mark pending messages as delivered ────────────────────────────────────
    try:
        db.execute(sql_text("""
            UPDATE messages m
            SET status = 'delivered'
            FROM conversations c
            WHERE m.conversation_id = c.id
              AND (
                c.user1_id = :uid OR c.user2_id = :uid
                OR EXISTS (
                    SELECT 1 FROM group_members gm
                    WHERE gm.conversation_id = c.id AND gm.user_id = :uid
                )
              )
              AND m.sender_id != :uid
              AND m.status = 'sent'
        """), {"uid": user_id})
        db.commit()

        newly_delivered = db.execute(sql_text("""
            SELECT DISTINCT m.sender_id, m.client_message_id, m.id
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            WHERE (
                c.user1_id = :uid OR c.user2_id = :uid
                OR EXISTS (
                    SELECT 1 FROM group_members gm
                    WHERE gm.conversation_id = c.id AND gm.user_id = :uid
                )
            )
              AND m.sender_id != :uid
              AND m.status = 'delivered'
        """), {"uid": user_id}).fetchall()

        for row in newly_delivered:
            sid = str(row[0])
            if sid in connections:
                try:
                    await connections[sid].send_text(json.dumps({
                        "type":              "status_update",
                        "client_message_id": str(row[1]) if row[1] else None,
                        "server_message_id": str(row[2]),
                        "status":            "delivered"
                    }))
                except Exception:
                    connections.pop(sid, None)
    except Exception as e:
        logger.error(f"[WS] Delivery update error: {e}")

    # ── Main loop ─────────────────────────────────────────────────────────────
    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
                continue

            msg_type = data.get("type")

            # ── Ping ──────────────────────────────────────────────────────────
            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            # ── Typing ────────────────────────────────────────────────────────
            if msg_type == "typing":
                receiver_id  = data.get("receiver_id")
                is_group_t   = data.get("is_group", False)
                conv_id_t    = data.get("conversation_id")

                if is_group_t and conv_id_t:
                    member_ids = await get_group_member_ids(db, conv_id_t, user_id)
                    for mid in member_ids:
                        if mid in connections:
                            try:
                                await connections[mid].send_text(json.dumps({
                                    "type":            "typing",
                                    "sender_id":       user_id,
                                    "conversation_id": conv_id_t
                                }))
                            except Exception:
                                connections.pop(mid, None)
                elif receiver_id and receiver_id in connections:
                    try:
                        await connections[receiver_id].send_text(json.dumps({
                            "type":      "typing",
                            "sender_id": user_id
                        }))
                    except Exception:
                        connections.pop(receiver_id, None)
                continue

            # ── Read receipt ──────────────────────────────────────────────────
            if msg_type == "read":
                conversation_id = data.get("conversation_id")
                sender_id       = data.get("sender_id")
                if conversation_id and sender_id:
                    try:
                        db.execute(sql_text("""
                            UPDATE messages
                            SET status = 'read'
                            WHERE conversation_id = :conv_id
                              AND sender_id = :sid
                              AND status != 'read'
                        """), {"conv_id": conversation_id, "sid": sender_id})
                        db.commit()
                        if sender_id in connections:
                            await connections[sender_id].send_text(json.dumps({
                                "type":            "status_update",
                                "status":          "read",
                                "conversation_id": conversation_id,
                                "read_by":         user_id
                            }))
                    except Exception as e:
                        logger.error(f"[WS] Read error: {e}")
                continue

            # ── Edit message ──────────────────────────────────────────────────
            if msg_type == "edit":
                server_message_id = data.get("server_message_id")
                new_content       = (data.get("content") or "").strip()
                receiver_id       = data.get("receiver_id")

                if server_message_id and new_content:
                    try:
                        msg = db.query(Message).filter(
                            Message.id        == uuid.UUID(server_message_id),
                            Message.sender_id == uuid.UUID(user_id),
                            Message.is_deleted == False
                        ).first()
                        if msg:
                            msg.content   = new_content
                            msg.is_edited = True
                            msg.edited_at = datetime.utcnow()
                            db.commit()

                            edit_payload = json.dumps({
                                "type":              "message_edited",
                                "server_message_id": server_message_id,
                                "content":           new_content
                            })

                            if msg.conversation_id:
                                conv_id_str = str(msg.conversation_id)
                                if await is_group_conversation(db, conv_id_str):
                                    member_ids = await get_group_member_ids(db, conv_id_str, user_id)
                                    for mid in member_ids:
                                        if mid in connections:
                                            try:
                                                await connections[mid].send_text(edit_payload)
                                            except Exception:
                                                connections.pop(mid, None)
                                elif receiver_id and receiver_id in connections:
                                    await connections[receiver_id].send_text(edit_payload)

                            await websocket.send_text(edit_payload)
                    except Exception as e:
                        logger.error(f"[WS] Edit error: {e}")
                continue

            # ── Reaction ──────────────────────────────────────────────────────
            if msg_type == "reaction":
                server_message_id = data.get("server_message_id")
                reaction          = data.get("reaction", "")
                receiver_id       = data.get("receiver_id")

                if server_message_id:
                    try:
                        msg = db.query(Message).filter(
                            Message.id == uuid.UUID(server_message_id)
                        ).first()
                        if msg:
                            msg.reaction = reaction if reaction else None
                            db.commit()

                            reaction_payload = json.dumps({
                                "type":              "reaction_update",
                                "server_message_id": server_message_id,
                                "reaction":          reaction,
                                "reactor_id":        user_id
                            })

                            if msg.conversation_id:
                                conv_id_str = str(msg.conversation_id)
                                if await is_group_conversation(db, conv_id_str):
                                    member_ids = await get_group_member_ids(db, conv_id_str, user_id)
                                    for mid in member_ids:
                                        if mid in connections:
                                            try:
                                                await connections[mid].send_text(reaction_payload)
                                            except Exception:
                                                connections.pop(mid, None)
                                elif receiver_id and receiver_id in connections:
                                    await connections[receiver_id].send_text(reaction_payload)

                            await websocket.send_text(reaction_payload)
                    except Exception as e:
                        logger.error(f"[WS] Reaction error: {e}")
                continue

            # ── Delete message ────────────────────────────────────────────────
            if msg_type == "delete":
                server_message_id = data.get("server_message_id")
                receiver_id       = data.get("receiver_id")

                if server_message_id:
                    try:
                        msg = db.query(Message).filter(
                            Message.id        == uuid.UUID(server_message_id),
                            Message.sender_id == uuid.UUID(user_id)
                        ).first()
                        if msg:
                            msg.is_deleted = True
                            msg.content    = None
                            msg.image_url  = None
                            db.commit()

                            delete_payload = json.dumps({
                                "type":              "message_deleted",
                                "server_message_id": server_message_id
                            })

                            if msg.conversation_id:
                                conv_id_str = str(msg.conversation_id)
                                if await is_group_conversation(db, conv_id_str):
                                    member_ids = await get_group_member_ids(db, conv_id_str, user_id)
                                    for mid in member_ids:
                                        if mid in connections:
                                            try:
                                                await connections[mid].send_text(delete_payload)
                                            except Exception:
                                                connections.pop(mid, None)
                                elif receiver_id and receiver_id in connections:
                                    await connections[receiver_id].send_text(delete_payload)

                            await websocket.send_text(delete_payload)
                    except Exception as e:
                        logger.error(f"[WS] Delete error: {e}")
                continue

            # ── Regular message ───────────────────────────────────────────────
            content           = (data.get("content") or "").strip()
            receiver_id       = str(data.get("receiver_id", ""))
            conversation_id   = data.get("conversation_id")
            client_message_id = data.get("client_message_id")
            image_url         = data.get("image_url")
            is_group_msg      = data.get("is_group", False)

            if not content and not image_url:
                continue
            if not is_group_msg and not receiver_id:
                continue

            # Rate limit
            if is_rate_limited(user_id):
                await websocket.send_text(json.dumps({
                    "type":              "error",
                    "client_message_id": client_message_id,
                    "message":           "Rate limit exceeded. Max 20 messages per minute."
                }))
                continue

            # Deduplication
            if client_message_id:
                existing = db.query(Message).filter(
                    Message.client_message_id == client_message_id
                ).first()
                if existing:
                    await websocket.send_text(json.dumps({
                        "type":              "ack",
                        "client_message_id": client_message_id,
                        "server_message_id": str(existing.id),
                        "status":            existing.status,
                        "timestamp":         existing.timestamp.isoformat()
                    }))
                    continue

            # Save to DB
            now = datetime.utcnow()
            try:
                msg = Message(
                    conversation_id   = uuid.UUID(str(conversation_id)) if conversation_id else None,
                    sender_id         = uuid.UUID(user_id),
                    content           = content or None,
                    timestamp         = now,
                    client_message_id = client_message_id,
                    status            = "sent",
                    image_url         = image_url or None
                )
                db.add(msg)
                db.commit()
                db.refresh(msg)
            except Exception as e:
                db.rollback()
                await websocket.send_text(json.dumps({
                    "type":              "error",
                    "client_message_id": client_message_id,
                    "message":           f"DB error: {str(e)}"
                }))
                continue

            # ACK to sender
            await websocket.send_text(json.dumps({
                "type":              "ack",
                "client_message_id": client_message_id,
                "server_message_id": str(msg.id),
                "status":            "sent",
                "timestamp":         now.isoformat()
            }))

            # Build payload
            msg_payload = json.dumps({
                "type":              "message",
                "sender_id":         user_id,
                "receiver_id":       receiver_id,
                "conversation_id":   str(msg.conversation_id) if msg.conversation_id else None,
                "server_message_id": str(msg.id),
                "client_message_id": client_message_id,
                "content":           content,
                "image_url":         image_url,
                "status":            "sent",
                "timestamp":         now.isoformat(),
                "is_group":          is_group_msg
            })

            # ── Deliver to group or single receiver ───────────────────────────
            if is_group_msg and conversation_id:
                member_ids    = await get_group_member_ids(db, str(conversation_id), user_id)
                delivered_cnt = 0
                for mid in member_ids:
                    if mid in connections:
                        try:
                            await connections[mid].send_text(msg_payload)
                            delivered_cnt += 1
                        except Exception:
                            logger.warning(f"[WS] Stale connection for {mid}")
                            connections.pop(mid, None)

                if delivered_cnt > 0:
                    msg.status = "delivered"
                    db.commit()
                    await websocket.send_text(json.dumps({
                        "type":              "status_update",
                        "client_message_id": client_message_id,
                        "server_message_id": str(msg.id),
                        "status":            "delivered"
                    }))
            else:
                logger.debug(f"[WS] Delivering to {receiver_id}. Online: {receiver_id in connections}")
                if receiver_id in connections:
                    try:
                        await connections[receiver_id].send_text(msg_payload)
                        msg.status = "delivered"
                        db.commit()
                        await websocket.send_text(json.dumps({
                            "type":              "status_update",
                            "client_message_id": client_message_id,
                            "server_message_id": str(msg.id),
                            "status":            "delivered"
                        }))
                    except Exception as e:
                        logger.warning(f"[WS] Stale connection for {receiver_id}: {e}")
                        connections.pop(receiver_id, None)

    except WebSocketDisconnect:
        connections.pop(user_id, None)
        await broadcast_online_status(user_id, False)
        logger.debug(f"[WS] {user_id} disconnected. Online: {len(connections)}")
        db.close()

    except Exception as e:
        logger.error(f"[WS] Error for {user_id}: {e}")
        connections.pop(user_id, None)
        await broadcast_online_status(user_id, False)
        db.close()