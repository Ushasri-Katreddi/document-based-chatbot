
from pathlib import Path

import pytest

from app.services.document_loader import load_document


def test_load_text_file(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text(
        "FastAPI builds APIs. PostgreSQL stores relational data.",
        encoding="utf-8",
    )

    documents = load_document(str(file_path))

    assert len(documents) == 1
    assert "FastAPI" in documents[0].page_content
    assert documents[0].metadata["source"] == "sample.txt"
    assert documents[0].metadata["file_type"] == "txt"


def test_load_missing_file_raises_error(tmp_path: Path):
    file_path = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        load_document(str(file_path))


def test_unsupported_file_type_raises_error(tmp_path: Path):
    file_path = tmp_path / "sample.docx"
    file_path.write_text("Test content", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file type"):
        load_document(str(file_path))
