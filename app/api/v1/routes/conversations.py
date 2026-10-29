
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conversation import Conversation
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.schemas.message import MessageResponse
from app.services.conversation_service import (
    create_conversation,
    list_conversations,
)
from app.services.message_service import create_message, list_messages
from app.services.qa_service import (
    answer_question,
    prepare_question_context,
    stream_answer,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])

# Temporary development identity. Replace with authenticated user identity later.
DEV_USER_ID = "local-user"


async def get_owned_conversation(
    db: AsyncSession,
    conversation_id: int,
) -> Conversation:
    """Return a conversation belonging to the development user."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == DEV_USER_ID,
        )
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return conversation


@router.post("/", response_model=ConversationResponse, status_code=201)
async def create_new_conversation(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """Create and persist a conversation."""
    return await create_conversation(db, DEV_USER_ID, payload)


@router.get("/", response_model=list[ConversationResponse])
async def get_conversations(
    db: AsyncSession = Depends(get_db),
) -> list[ConversationResponse]:
    """List conversations belonging to the development user."""
    return await list_conversations(db, DEV_USER_ID)


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
async def get_conversation_messages(
    conversation_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> list[MessageResponse]:
    """Retrieve messages for an existing conversation."""
    await get_owned_conversation(db, conversation_id)
    return await list_messages(db, conversation_id)


@router.post(
    "/{conversation_id}/chat",
    response_model=ChatResponse,
)
async def chat_with_documents(
    payload: ChatRequest,
    conversation_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Answer a question using retrieved documents and persist chat history."""
    await get_owned_conversation(db, conversation_id)

    try:
        result = answer_question(
            question=payload.question,
            document_id=payload.document_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await create_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=payload.question,
    )

    await create_message(
        db=db,
        conversation_id=conversation_id,
        role="assistant",
        content=result.answer,
        citations=[
            citation.model_dump() for citation in result.citations
        ],
    )

    return result



@router.post("/{conversation_id}/chat/stream")
async def stream_chat_with_documents(
    payload: ChatRequest,
    conversation_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream an answer and persist completed chat messages."""
    await get_owned_conversation(db, conversation_id)

    if not payload.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    async def generate() -> AsyncIterator[str]:
        full_answer: list[str] = []

        try:
            # Retrieve document context and citations once.
            context, citations = prepare_question_context(
                question=payload.question,
                document_id=payload.document_id,
            )

            # Stream the answer using the prepared context.
            for text_chunk in stream_answer(
                question=payload.question,
                document_id=payload.document_id,
                context=context,
            ):
                full_answer.append(text_chunk)
                yield (
                    f"data: {json.dumps({'type': 'token', 'content': text_chunk})}\n\n"
                )

            # Persist the user question.
            await create_message(
                db=db,
                conversation_id=conversation_id,
                role="user",
                content=payload.question,
            )

            # Persist the complete answer and its citations.
            await create_message(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content="".join(full_answer),
                citations=[
                    citation.model_dump() for citation in citations
                ],
            )

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception:
            await db.rollback()
            yield (
                f"data: {json.dumps({'type': 'error', 'message': 'Unable to generate or save the answer.'})}\n\n"
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
