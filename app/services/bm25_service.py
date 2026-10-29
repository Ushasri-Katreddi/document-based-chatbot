

import re

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from app.services.vector_store import get_all_stored_documents

def tokenize_text(text: str) -> list[str]:
    """Convert text into lowercase word tokens for BM25."""
    return re.findall(r"\b\w+\b", text.lower())


def retrieve_with_bm25(
    question: str,
    documents: list[Document],
    k: int = 4,
) -> list[Document]:
    """Rank a supplied document corpus using BM25 keyword relevance."""
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    if k < 1:
        raise ValueError("k must be at least 1.")

    if not documents:
        return []

    tokenized_corpus = [
        tokenize_text(document.page_content)
        for document in documents
    ]

    # BM25 requires a non-empty tokenized corpus.
    non_empty_indices = [
        index
        for index, tokens in enumerate(tokenized_corpus)
        if tokens
    ]

    if not non_empty_indices:
        return []

    valid_documents = [documents[index] for index in non_empty_indices]
    valid_corpus = [tokenized_corpus[index] for index in non_empty_indices]

    bm25 = BM25Okapi(valid_corpus)
    query_tokens = tokenize_text(question)

    if not query_tokens:
        return []

    scores = bm25.get_scores(query_tokens)

    ranked_indices = sorted(
        range(len(valid_documents)),
        key=lambda index: scores[index],
        reverse=True,
    )

    return [
        valid_documents[index]
        for index in ranked_indices[:k]
        if scores[index] > 0
    ]
def retrieve_stored_documents_with_bm25(
    question: str,
    document_id: int | None = None,
    k: int = 4,
) -> list[Document]:
    """Retrieve stored document chunks using BM25 keyword relevance."""
    documents = get_all_stored_documents(document_id=document_id)

    return retrieve_with_bm25(
        question=question,
        documents=documents,
        k=k,
    )