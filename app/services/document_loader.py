from pathlib import Path

from langchain_core.documents import Document as LangChainDocument
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
)


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def load_document(file_path: str) -> list[LangChainDocument]:
    """Load a supported file and return its content as LangChain documents."""
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Document not found: {path.name}")

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            "Supported types are PDF, TXT, and Markdown."
        )

    if extension == ".pdf":
        documents = PyPDFLoader(str(path)).load()
    else:
        documents = TextLoader(
            str(path),
            encoding="utf-8",
            autodetect_encoding=True,
        ).load()

    for document in documents:
        document.metadata["source"] = path.name
        document.metadata["file_type"] = extension.lstrip(".")

    return documents