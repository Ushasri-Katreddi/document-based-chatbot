
from langchain_core.documents import Document

from app.services.document_loader import load_document
from app.services.text_splitter import split_documents
from app.services.vector_store import get_vector_store


def ingest_document(
    file_path: str,
    document_id: int,
) -> int:
    """Load, split, embed, and store a document's chunks."""
    documents = load_document(file_path)
    chunks = split_documents(documents)

    for chunk in chunks:
        chunk.metadata["document_id"] = document_id

    if not chunks:
        raise ValueError("The document contains no text to index.")

    vector_store = get_vector_store()
    vector_store.add_documents(chunks)

    return len(chunks)
