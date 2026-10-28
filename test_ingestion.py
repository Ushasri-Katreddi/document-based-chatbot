
from app.services.ingestion_service import ingest_document
from app.services.vector_store import get_vector_store

file_path = "sample.txt"
document_id = 999

try:
    chunk_count = ingest_document(file_path, document_id)
    print(f"Successfully ingested document. Chunks created: {chunk_count}")

    vector_store = get_vector_store()
    results = vector_store.similarity_search(
        "Which database stores structured data?",
        k=3,
        filter={"document_id": document_id},
    )

    print(f"\nRetrieved chunks: {len(results)}")
    for index, result in enumerate(results, start=1):
        print(f"\nChunk {index}: {result.page_content}")
        print(f"Metadata: {result.metadata}")

except Exception as error:
    print(f"Test failed: {type(error).__name__}: {error}")
    raise
