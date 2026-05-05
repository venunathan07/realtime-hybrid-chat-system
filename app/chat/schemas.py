from pydantic import BaseModel

class MessageSchema(BaseModel):
    conversation_id: int
    content: str