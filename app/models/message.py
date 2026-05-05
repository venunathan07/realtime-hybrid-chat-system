import uuid
from sqlalchemy import Column, ForeignKey, Text, DateTime, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id   = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    sender_id         = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    content           = Column(Text, nullable=True)
    timestamp         = Column(DateTime, default=datetime.utcnow)
    client_message_id = Column(String, unique=True, nullable=True, index=True)
    status            = Column(String, default="sent")
    image_url         = Column(String, nullable=True)
    reaction          = Column(String, nullable=True)
    is_deleted        = Column(Boolean, default=False)
    is_edited         = Column(Boolean, default=False)
    edited_at         = Column(DateTime, nullable=True)