
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


async def create_message(
    db: AsyncSession,
    conversation_id: int,
    role: str,
    content: str,
    citations: list[dict] | None = None,
) -> Message:
    """Persist a message in PostgreSQL."""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        citations=citations,
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)

    return message


async def list_messages(
    db: AsyncSession,
    conversation_id: int,
) -> list[Message]:
    """Retrieve a conversation's messages in chronological order."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
    )

    return list(result.scalars().all())
