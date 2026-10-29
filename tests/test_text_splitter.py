
from langchain_core.documents import Document

from app.services.text_splitter import split_documents


def test_split_documents_returns_chunks():
    document = Document(
        page_content="FastAPI is a Python framework. " * 100,
        metadata={"source": "sample.txt"},
    )

    chunks = split_documents([document])

    assert len(chunks) > 1
    assert all(chunk.page_content.strip() for chunk in chunks)


def test_split_documents_preserves_source_metadata():
    document = Document(
        page_content="PostgreSQL stores structured data. " * 100,
        metadata={"source": "database.txt"},
    )

    chunks = split_documents([document])

    assert chunks
    assert all(
        chunk.metadata.get("source") == "database.txt"
        for chunk in chunks
    )


def test_split_documents_handles_empty_input():
    chunks = split_documents([])

    assert chunks == []
