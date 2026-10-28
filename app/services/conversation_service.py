
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate


async def create_conversation(
    db: AsyncSession,
    user_id: str,
    data: ConversationCreate,
) -> Conversation:
    """Create and persist a conversation in PostgreSQL."""
    conversation = Conversation(
        title=data.title,
        user_id=user_id,
    )

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return conversation


async def list_conversations(
    db: AsyncSession,
    user_id: str,
) -> list[Conversation]:
    """List conversations belonging to one user."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
    )

    return list(result.scalars().all())
