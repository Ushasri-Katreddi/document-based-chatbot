
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.chat import Citation


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
