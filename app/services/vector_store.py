
from langchain_chroma import Chroma

from app.config import settings
from app.services.embedding_service import get_embedding_model


def get_vector_store() -> Chroma:
    """Create or connect to the persistent local ChromaDB store."""
    embedding_model = get_embedding_model()

    return Chroma(
        collection_name="document_chunks",
        embedding_function=embedding_model,
        persist_directory=settings.chroma_persist_directory,
    )
