import uuid
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.group_member import GroupMember
from app.auth.jwt_handler import get_current_user

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class CreateGroupRequest(BaseModel):
    name: str
    member_ids: List[str]

class EditMessageRequest(BaseModel):
    content: str


# ── Start or get existing DM conversation ────────────────────────────────────
@router.post("/chat/start/{other_user_id}")
def start_chat(
    other_user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        other_uuid = str(uuid.UUID(other_user_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    current_uuid = str(current_user.id)

    result = db.execute(text("""
        SELECT id FROM conversations
        WHERE (user1_id = :a AND user2_id = :b)
           OR (user1_id = :b AND user2_id = :a)
           AND (is_group = FALSE OR is_group IS NULL)
        LIMIT 1
    """), {"a": current_uuid, "b": other_uuid}).fetchone()

    if result:
        return {"conversation_id": str(result[0])}

    new_id = str(uuid.uuid4())
    db.execute(text("""
        INSERT INTO conversations (id, user1_id, user2_id, is_group)
        VALUES (:id, :user1, :user2, FALSE)
    """), {"id": new_id, "user1": current_uuid, "user2": other_uuid})
    db.commit()
    return {"conversation_id": new_id}


# ── Create group conversation ─────────────────────────────────────────────────
@router.post("/chat/group/create")
def create_group(
    data: CreateGroupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="Group name required")
    if len(data.member_ids) < 1:
        raise HTTPException(status_code=400, detail="Add at least one member")

    conv_id = str(uuid.uuid4())
    db.execute(text("""
        INSERT INTO conversations (id, is_group, name)
        VALUES (:id, TRUE, :name)
    """), {"id": conv_id, "name": data.name.strip()})

    # Add creator + all selected members
    all_member_ids = list(set([str(current_user.id)] + data.member_ids))
    for uid in all_member_ids:
        try:
            uuid.UUID(uid)
        except ValueError:
            continue
        db.execute(text("""
            INSERT INTO group_members (id, conversation_id, user_id, joined_at)
            VALUES (:id, :conv_id, :user_id, NOW())
        """), {"id": str(uuid.uuid4()), "conv_id": conv_id, "user_id": uid})

    db.commit()
    return {"conversation_id": conv_id, "name": data.name.strip()}


# ── Get group members ─────────────────────────────────────────────────────────
@router.get("/chat/group/{conv_id}/members")
def get_group_members(
    conv_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        conv_uuid = str(uuid.UUID(conv_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    rows = db.execute(text("""
        SELECT u.id, u.username
        FROM group_members gm
        JOIN users u ON u.id = gm.user_id
        WHERE gm.conversation_id = :cid
    """), {"cid": conv_uuid}).fetchall()

    return [{"id": str(r[0]), "username": r[1]} for r in rows]


# ── Get message history ───────────────────────────────────────────────────────
@router.get("/chat/messages/{conversation_id}")
def get_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        conv_uuid = str(uuid.UUID(conversation_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    current_uuid = str(current_user.id)

    # Check access — DM or group member
    conv = db.execute(text("""
        SELECT id FROM conversations
        WHERE id = :conv_id
          AND (
            user1_id = :uid OR user2_id = :uid
            OR EXISTS (
                SELECT 1 FROM group_members gm
                WHERE gm.conversation_id = :conv_id AND gm.user_id = :uid
            )
          )
    """), {"conv_id": conv_uuid, "uid": current_uuid}).fetchone()

    if not conv:
        raise HTTPException(status_code=403, detail="Not your conversation")

    messages = db.execute(text("""
        SELECT id, sender_id, conversation_id, content,
               timestamp, status, client_message_id,
               image_url, reaction, is_deleted, is_edited
        FROM messages
        WHERE conversation_id = :conv_id
        ORDER BY timestamp ASC
    """), {"conv_id": conv_uuid}).fetchall()

    return [
        {
            "id":                str(m[0]),
            "sender_id":         str(m[1]),
            "conversation_id":   str(m[2]),
            "content":           m[3] if not m[9] else "🗑️ This message was deleted",
            "timestamp":         m[4].isoformat() if m[4] else None,
            "status":            m[5] or "sent",
            "client_message_id": str(m[6]) if m[6] else None,
            "image_url":         m[7] if not m[9] else None,
            "reaction":          m[8],
            "is_deleted":        m[9] or False,
            "is_edited":         m[10] or False,
        }
        for m in messages
    ]


# ── Edit message ──────────────────────────────────────────────────────────────
@router.put("/chat/message/{message_id}")
def edit_message(
    message_id: str,
    data: EditMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        msg_uuid = str(uuid.UUID(message_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID")

    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    msg = db.query(Message).filter(Message.id == msg_uuid).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if str(msg.sender_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Cannot edit someone else's message")
    if msg.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot edit a deleted message")

    from datetime import datetime
    msg.content   = data.content.strip()
    msg.is_edited = True
    msg.edited_at = datetime.utcnow()
    db.commit()

    return {"message": "Edited", "id": message_id, "content": msg.content}


# ── Get unread messages ───────────────────────────────────────────────────────
@router.get("/chat/unread")
def get_unread_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    uid = str(current_user.id)
    messages = db.execute(text("""
        SELECT m.id, m.content, m.sender_id, m.timestamp,
               m.status, m.conversation_id, m.client_message_id,
               m.image_url, m.reaction, m.is_deleted
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
        AND m.status = 'sent'
        ORDER BY m.timestamp ASC
    """), {"uid": uid}).fetchall()

    return [
        {
            "id":                str(m[0]),
            "content":           m[1] if not m[9] else "🗑️ This message was deleted",
            "sender_id":         str(m[2]),
            "timestamp":         m[3].isoformat() if m[3] else None,
            "status":            m[4],
            "conversation_id":   str(m[5]),
            "client_message_id": str(m[6]) if m[6] else None,
            "image_url":         m[7] if not m[9] else None,
            "reaction":          m[8],
            "is_deleted":        m[9] or False
        }
        for m in messages
    ]


# ── Mark messages as read ─────────────────────────────────────────────────────
@router.post("/chat/read/{conversation_id}")
def mark_as_read(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        conv_uuid = str(uuid.UUID(conversation_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    db.execute(text("""
        UPDATE messages
        SET status = 'read'
        WHERE conversation_id = :conv_id
          AND sender_id != :uid
          AND status != 'read'
    """), {"conv_id": conv_uuid, "uid": str(current_user.id)})
    db.commit()
    return {"message": "Marked as read"}


# ── Get conversations (DMs + groups) ─────────────────────────────────────────
@router.get("/chat/conversations")
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    uid = str(current_user.id)
    result = []

    # DM conversations
    dm_rows = db.execute(text("""
        SELECT
            c.id, c.user1_id, c.user2_id,
            m.content AS last_message,
            m.timestamp AS last_timestamp,
            m.status AS last_status,
            COUNT(unread.id) AS unread_count
        FROM conversations c
        LEFT JOIN LATERAL (
            SELECT content, timestamp, status
            FROM messages
            WHERE conversation_id = c.id
            ORDER BY timestamp DESC
            LIMIT 1
        ) m ON true
        LEFT JOIN messages unread
            ON  unread.conversation_id = c.id
            AND unread.sender_id != :uid
            AND unread.status = 'sent'
        WHERE (c.user1_id = :uid OR c.user2_id = :uid)
          AND (c.is_group = FALSE OR c.is_group IS NULL)
        GROUP BY c.id, c.user1_id, c.user2_id,
                 m.content, m.timestamp, m.status
        ORDER BY m.timestamp DESC NULLS LAST
    """), {"uid": uid}).fetchall()

    for row in dm_rows:
        other_id = str(row[2]) if str(row[1]) == uid else str(row[1])
        other_user = db.execute(text(
            "SELECT username FROM users WHERE id = :id"
        ), {"id": other_id}).fetchone()
        result.append({
            "conversation_id": str(row[0]),
            "is_group":        False,
            "other_user_id":   other_id,
            "other_username":  other_user[0] if other_user else "Unknown",
            "last_message":    row[3] or "",
            "last_timestamp":  row[4].isoformat() if row[4] else None,
            "last_status":     row[5] or "",
            "unread_count":    row[6] or 0
        })

    # Group conversations
    group_rows = db.execute(text("""
        SELECT
            c.id, c.name,
            m.content AS last_message,
            m.timestamp AS last_timestamp,
            m.status AS last_status,
            COUNT(unread.id) AS unread_count
        FROM conversations c
        JOIN group_members gm ON gm.conversation_id = c.id AND gm.user_id = :uid
        LEFT JOIN LATERAL (
            SELECT content, timestamp, status
            FROM messages
            WHERE conversation_id = c.id
            ORDER BY timestamp DESC
            LIMIT 1
        ) m ON true
        LEFT JOIN messages unread
            ON  unread.conversation_id = c.id
            AND unread.sender_id != :uid
            AND unread.status = 'sent'
        WHERE c.is_group = TRUE
        GROUP BY c.id, c.name, m.content, m.timestamp, m.status
        ORDER BY m.timestamp DESC NULLS LAST
    """), {"uid": uid}).fetchall()

    for row in group_rows:
        member_count = db.execute(text(
            "SELECT COUNT(*) FROM group_members WHERE conversation_id = :cid"
        ), {"cid": str(row[0])}).scalar()
        result.append({
            "conversation_id": str(row[0]),
            "is_group":        True,
            "group_name":      row[1],
            "member_count":    member_count,
            "last_message":    row[2] or "",
            "last_timestamp":  row[3].isoformat() if row[3] else None,
            "last_status":     row[4] or "",
            "unread_count":    row[5] or 0
        })

    result.sort(key=lambda x: x.get("last_timestamp") or "", reverse=True)
    return result


# ── Search messages ───────────────────────────────────────────────────────────
@router.get("/chat/search/{conversation_id}")
def search_messages(
    conversation_id: str,
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        conv_uuid = str(uuid.UUID(conversation_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    if not q or len(q.strip()) < 1:
        return []

    current_uuid = str(current_user.id)

    conv = db.execute(text("""
        SELECT id FROM conversations
        WHERE id = :conv_id
          AND (
            user1_id = :uid OR user2_id = :uid
            OR EXISTS (
                SELECT 1 FROM group_members gm
                WHERE gm.conversation_id = :conv_id AND gm.user_id = :uid
            )
          )
    """), {"conv_id": conv_uuid, "uid": current_uuid}).fetchone()

    if not conv:
        raise HTTPException(status_code=403, detail="Not your conversation")

    messages = db.execute(text("""
        SELECT id, sender_id, content, timestamp,
               status, client_message_id, image_url, reaction, is_deleted, is_edited
        FROM messages
        WHERE conversation_id = :conv_id
          AND is_deleted = false
          AND LOWER(content) LIKE LOWER(:query)
        ORDER BY timestamp ASC
        LIMIT 50
    """), {"conv_id": conv_uuid, "query": f"%{q.strip()}%"}).fetchall()

    return [
        {
            "id":                str(m[0]),
            "sender_id":         str(m[1]),
            "content":           m[2],
            "timestamp":         m[3].isoformat() if m[3] else None,
            "status":            m[4],
            "client_message_id": str(m[5]) if m[5] else None,
            "image_url":         m[6],
            "reaction":          m[7],
            "is_deleted":        m[8],
            "is_edited":         m[9] or False
        }
        for m in messages
    ]


# ── Delete message (soft delete) ──────────────────────────────────────────────
@router.delete("/chat/message/{message_id}")
def delete_message(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        msg_uuid = str(uuid.UUID(message_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID")

    msg = db.query(Message).filter(Message.id == msg_uuid).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if str(msg.sender_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Cannot delete someone else's message")

    msg.is_deleted = True
    msg.content    = None
    msg.image_url  = None
    db.commit()

    return {"message": "Deleted", "id": message_id}


# ── React to message ──────────────────────────────────────────────────────────
@router.post("/chat/react/{message_id}")
def react_to_message(
    message_id: str,
    reaction: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        msg_uuid = str(uuid.UUID(message_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID")

    allowed = ["❤️", "👍", "😂", "😮", "😢", "🔥", ""]
    if reaction not in allowed:
        raise HTTPException(status_code=400, detail="Invalid reaction")

    msg = db.query(Message).filter(Message.id == msg_uuid).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    msg.reaction = reaction if reaction else None
    db.commit()

    return {"message": "Reaction updated", "reaction": reaction, "id": message_id}


# ── Upload image ──────────────────────────────────────────────────────────────
@router.post("/chat/upload")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only images allowed (JPEG, PNG, GIF, WebP)")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large. Max 5MB.")

    ext      = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    return {"image_url": f"/uploads/{filename}"}


# ── Online users ──────────────────────────────────────────────────────────────
@router.get("/chat/online")
def get_online_users(
    current_user: User = Depends(get_current_user)
):
    from app.chat.websocket import connections
    return {"online_users": list(connections.keys())}