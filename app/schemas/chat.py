
from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: int
    source: str
    chunk_index: int = Field(ge=1)


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
