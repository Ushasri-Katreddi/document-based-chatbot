
from langchain_core.documents import Document

from app.services.vector_store import get_vector_store


def retrieve_documents(
    question: str,
    document_id: int | None = None,
    k: int = 4,
) -> list[Document]:
    """Retrieve relevant document chunks for a user's question."""
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    if k < 1:
        raise ValueError("k must be at least 1.")

    vector_store = get_vector_store()

    search_kwargs: dict = {"k": k}

    if document_id is not None:
        search_kwargs["filter"] = {"document_id": document_id}

    return vector_store.similarity_search(
        question,
        **search_kwargs,
    )
