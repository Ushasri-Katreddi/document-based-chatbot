
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings


def get_embedding_model() -> HuggingFaceEmbeddings:
    """Create the local sentence-transformer embedding model."""
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
