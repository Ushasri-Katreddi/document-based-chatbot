
import pytest
from langchain_core.documents import Document

from app.services.bm25_service import (
    retrieve_with_bm25,
    tokenize_text,
)


def test_tokenize_text_lowercases_and_splits_words():
    tokens = tokenize_text("Python, FASTAPI and Java!")

    assert tokens == ["python", "fastapi", "and", "java"]


def test_bm25_ranks_relevant_document_first():
    documents = [
        Document(
            page_content="Python developer builds APIs with FastAPI.",
            metadata={"document_id": 1, "chunk_index": 0},
        ),
        Document(
            page_content="Java developer builds enterprise applications.",
            metadata={"document_id": 2, "chunk_index": 0},
        ),
        Document(
            page_content="Gardening and cooking are relaxing hobbies.",
            metadata={"document_id": 3, "chunk_index": 0},
        ),
    ]

    results = retrieve_with_bm25(
        question="Python FastAPI",
        documents=documents,
        k=2,
    )

    assert results
    assert results[0].metadata["document_id"] == 1


def test_bm25_returns_empty_list_for_empty_corpus():
    results = retrieve_with_bm25(
        question="Python",
        documents=[],
    )

    assert results == []


def test_bm25_rejects_empty_question():
    with pytest.raises(ValueError, match="Question cannot be empty"):
        retrieve_with_bm25(
            question="   ",
            documents=[],
        )


def test_bm25_rejects_invalid_k():
    with pytest.raises(ValueError, match="k must be at least 1"):
        retrieve_with_bm25(
            question="Python",
            documents=[],
            k=0,
        )
