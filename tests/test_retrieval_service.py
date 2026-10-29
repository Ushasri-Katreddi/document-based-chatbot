
import pytest
from langchain_core.documents import Document

import app.services.retrieval_service as retrieval_service


def make_document(document_id: int, chunk_index: int) -> Document:
    return Document(
        page_content=f"Content for document {document_id}, chunk {chunk_index}",
        metadata={
            "document_id": document_id,
            "chunk_index": chunk_index,
            "source": f"document_{document_id}.pdf",
        },
    )


def test_hybrid_retrieval_combines_both_rankings(monkeypatch):
    vector_results = [
        make_document(1, 0),
        make_document(1, 1),
    ]
    bm25_results = [
        make_document(1, 1),
        make_document(1, 0),
    ]

    monkeypatch.setattr(
        retrieval_service,
        "retrieve_documents",
        lambda **kwargs: vector_results,
    )
    monkeypatch.setattr(
        retrieval_service,
        "retrieve_stored_documents_with_bm25",
        lambda **kwargs: bm25_results,
    )

    results = retrieval_service.retrieve_hybrid_documents(
        question="Python APIs",
        k=2,
    )

    assert len(results) == 2
    assert {doc.metadata["chunk_index"] for doc in results} == {0, 1}


def test_hybrid_retrieval_deduplicates_shared_chunks(monkeypatch):
    shared_chunk = make_document(1, 0)

    monkeypatch.setattr(
        retrieval_service,
        "retrieve_documents",
        lambda **kwargs: [shared_chunk],
    )
    monkeypatch.setattr(
        retrieval_service,
        "retrieve_stored_documents_with_bm25",
        lambda **kwargs: [shared_chunk],
    )

    results = retrieval_service.retrieve_hybrid_documents(
        question="Python",
        k=4,
    )

    assert len(results) == 1
    assert results[0].metadata["chunk_index"] == 0


def test_hybrid_retrieval_passes_document_filter(monkeypatch):
    received_ids = []

    def fake_vector_search(**kwargs):
        received_ids.append(kwargs["document_id"])
        return [make_document(5, 0)]

    def fake_bm25_search(**kwargs):
        received_ids.append(kwargs["document_id"])
        return [make_document(5, 0)]

    monkeypatch.setattr(
        retrieval_service,
        "retrieve_documents",
        fake_vector_search,
    )
    monkeypatch.setattr(
        retrieval_service,
        "retrieve_stored_documents_with_bm25",
        fake_bm25_search,
    )

    retrieval_service.retrieve_hybrid_documents(
        question="Python",
        document_id=5,
    )

    assert received_ids == [5, 5]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"question": "   "}, "Question cannot be empty"),
        ({"question": "Python", "k": 0}, "k must be at least 1"),
        (
            {"question": "Python", "fetch_k": 0},
            "fetch_k must be at least 1",
        ),
        (
            {"question": "Python", "rrf_constant": 0},
            "rrf_constant must be at least 1",
        ),
    ],
)
def test_hybrid_retrieval_validates_inputs(kwargs, message):
    with pytest.raises(ValueError, match=message):
        retrieval_service.retrieve_hybrid_documents(**kwargs)
