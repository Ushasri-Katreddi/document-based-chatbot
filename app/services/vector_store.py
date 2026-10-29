
from langchain_chroma import Chroma

from app.config import settings
from app.services.embedding_service import get_embedding_model
from langchain_core.documents import Document
from langchain_chroma import Chroma

def get_vector_store() -> Chroma:
    """Create or connect to the persistent local ChromaDB store."""
    embedding_model = get_embedding_model()

    return Chroma(
        collection_name="document_chunks",
        embedding_function=embedding_model,
        persist_directory=settings.chroma_persist_directory,
    )

from langchain_core.documents import Document


def get_all_stored_documents(
    document_id: int | None = None,
) -> list[Document]:
    """Load stored document chunks from ChromaDB for lexical retrieval."""
    vector_store = get_vector_store()

    filters = (
        {"document_id": document_id}
        if document_id is not None
        else None
    )

    result = vector_store.get(
        where=filters,
        include=["documents", "metadatas"],
    )

    documents = result.get("documents") or []
    metadatas = result.get("metadatas") or []

    return [
        Document(
            page_content=content,
            metadata=metadata or {},
        )
        for content, metadata in zip(documents, metadatas)
        if content
    ]
