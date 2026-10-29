
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

from app.services.bm25_service import (
    retrieve_stored_documents_with_bm25,
)


def retrieve_hybrid_documents(
    question: str,
    document_id: int | None = None,
    k: int = 4,
    fetch_k: int = 10,
    rrf_constant: int = 60,
) -> list[Document]:
    """Combine vector and BM25 rankings using Reciprocal Rank Fusion."""
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    if k < 1:
        raise ValueError("k must be at least 1.")

    if fetch_k < 1:
        raise ValueError("fetch_k must be at least 1.")

    if rrf_constant < 1:
        raise ValueError("rrf_constant must be at least 1.")

    # Retrieve candidates independently from both retrieval systems.
    vector_results = retrieve_documents(
        question=question,
        document_id=document_id,
        k=fetch_k,
    )

    bm25_results = retrieve_stored_documents_with_bm25(
        question=question,
        document_id=document_id,
        k=fetch_k,
    )

    # Use document identity to merge rankings without duplicate chunks.
    fused_scores: dict[tuple, float] = {}
    documents_by_key: dict[tuple, Document] = {}

    for results in (vector_results, bm25_results):
        seen_in_ranking: set[tuple] = set()

        for rank, document in enumerate(results, start=1):
            metadata = document.metadata

            # These fields identify a stored chunk in this project.
            key = (
                metadata.get("document_id"),
                metadata.get("chunk_index"),
                metadata.get("source"),
            )

            # Avoid double-counting a chunk if a ranking contains duplicates.
            if key in seen_in_ranking:
                continue

            seen_in_ranking.add(key)
            documents_by_key.setdefault(key, document)
            fused_scores[key] = fused_scores.get(key, 0.0) + (
                1.0 / (rrf_constant + rank)
            )

    ranked_keys = sorted(
        fused_scores,
        key=lambda key: fused_scores[key],
        reverse=True,
    )

    return [
        documents_by_key[key]
        for key in ranked_keys[:k]
    ]
