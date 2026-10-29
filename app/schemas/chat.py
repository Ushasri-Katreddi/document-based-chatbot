
from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: int
    source: str
    chunk_index: int = Field(ge=1)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    document_id: int | None = Field(default=None, gt=0)


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
