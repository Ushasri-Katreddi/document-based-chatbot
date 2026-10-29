
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageCreate(BaseModel):
    role: str
    content: str
    citations: list[dict[str, Any]] = Field(default_factory=list)


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("citations", mode="before")
    @classmethod
    def normalize_citations(cls, value: Any) -> list:
        """Convert legacy NULL citation values to an empty list."""
        return value if value is not None else []
