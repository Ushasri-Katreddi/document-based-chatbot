
from langchain_groq import ChatGroq

from app.config import settings


def get_llm() -> ChatGroq:
    """Create the configured Groq chat model."""
    if not settings.groq_api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. Configure it in your .env file."
        )

    return ChatGroq(
        model=settings.llm_model,
        api_key=settings.groq_api_key,
        temperature=0,
        max_retries=2,
        streaming=True,
    )
