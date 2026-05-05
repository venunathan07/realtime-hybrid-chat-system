import uuid
from sqlalchemy import Column, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.base import Base


class GroupMember(Base):
    __tablename__ = "group_members"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    joined_at       = Column(DateTime, default=datetime.utcnow)