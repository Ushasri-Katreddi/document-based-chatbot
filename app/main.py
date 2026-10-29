
from fastapi import FastAPI

from app.api.v1.routes.documents import router as documents_router
from app.api.v1.routes.conversations import router as conversations_router
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    description=(
        "A document-grounded chatbot using RAG, LangChain, "
        "PostgreSQL, and ChromaDB."
    ),
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Check whether the API application is running."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
    }


app.include_router(documents_router)
app.include_router(conversations_router)
