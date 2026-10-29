
from app.services.document_loader import load_document
from app.services.text_splitter import split_documents
from app.services.vector_store import get_vector_store


def ingest_document(
    file_path: str,
    document_id: int,
    source_filename: str | None = None,
) -> int:
    """Load, split, embed, and store a document's chunks."""

    documents = load_document(file_path)
    chunks = split_documents(documents)

    if not chunks:
        raise ValueError("The document contains no text to index.")

    for chunk_index, chunk in enumerate(chunks, start=1):
        chunk.metadata["document_id"] = document_id
        chunk.metadata["chunk_index"] = chunk_index

        if source_filename:
            chunk.metadata["source"] = source_filename

    vector_store = get_vector_store()
    vector_store.add_documents(chunks)

    return len(chunks)
