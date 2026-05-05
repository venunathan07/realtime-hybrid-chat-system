import uuid
from sqlalchemy import Column, ForeignKey, Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user1_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    user2_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_group = Column(Boolean, default=False)
    name     = Column(String, nullable=True)