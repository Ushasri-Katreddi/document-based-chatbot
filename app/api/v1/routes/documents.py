
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi import Path as FastAPIPath
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse
from app.services.ingestion_service import ingest_document
from app.services.vector_store import get_vector_store


router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = Path("data/uploads")
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload a document, save its metadata, and index its contents."""
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if not filename or extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, TXT, and Markdown files are supported.",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = UPLOAD_DIR / f"{uuid4().hex}{extension}"
    document = None

    try:
        content = await file.read(MAX_FILE_SIZE + 1)

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File size must not exceed 10 MB.",
            )

        stored_path.write_bytes(content)

        document = Document(
            filename=filename,
            file_type=extension.lstrip("."),
            file_path=str(stored_path),
            status="processing",
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        chunk_count = ingest_document(
    file_path=str(stored_path),
    document_id=document.id,
    source_filename=document.filename,
)

        document.status = "ready"
        await db.commit()

        return {
            "id": document.id,
            "filename": document.filename,
            "status": document.status,
            "chunks_created": chunk_count,
        }

    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()

        if document is not None:
            try:
                await db.delete(document)
                await db.commit()
            except Exception:
                await db.rollback()

        stored_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Document processing failed.",
        ) from exc
    finally:
        await file.close()


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
) -> list[Document]:
    """List uploaded documents."""
    result = await db.execute(
        select(Document).order_by(Document.uploaded_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int = FastAPIPath(gt=0),
    db: AsyncSession = Depends(get_db),
) -> Document:
    """Retrieve one document by its database ID."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return document


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: int = FastAPIPath(gt=0),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document and its indexed chunks."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    # Remove indexed chunks belonging to this document.
    vector_store = get_vector_store()
    vector_store.delete(where={"document_id": document_id})

    # Remove the uploaded file.
    file_path = Path(document.file_path)
    file_path.unlink(missing_ok=True)

    # Remove the database record.
    await db.delete(document)
    await db.commit()




