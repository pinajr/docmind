import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pymupdf
from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models import Document


MAX_FILE_SIZE = 20 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024
STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage"


class DocumentProcessingError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DocumentNotFoundError(Exception):
    pass


def get_document(document_id: str, db: Session) -> Document:
    """Find a document in the database by its UUID."""
    try:
        # Parse and normalize the identifier
        document_uuid = UUID(document_id)
    except (ValueError, AttributeError) as exc:
        raise DocumentNotFoundError from exc

    document = db.get(Document, document_uuid)
    if document is None:
        raise DocumentNotFoundError
    return document


async def _read_pdf_upload(file: UploadFile) -> bytes:
    """Read an upload in bounded chunks so oversized files are rejected early."""
    content = bytearray()
    while chunk := await file.read(CHUNK_SIZE):
        content.extend(chunk)
        if len(content) > MAX_FILE_SIZE:
            raise DocumentProcessingError("PDF must be 20 MB or smaller.", 413)
    return bytes(content)


async def save_and_extract_pdf(file: UploadFile, db: Session) -> Document:
    content = await _read_pdf_upload(file)
    if not content.startswith(b"%PDF-"):
        raise DocumentProcessingError("The uploaded file is not a valid PDF.")

    try:
        with pymupdf.open(stream=content, filetype="pdf") as pdf:
            if pdf.is_encrypted:
                raise DocumentProcessingError("Password-protected PDFs are not supported.")
            extracted_text = "\n\n".join(page.get_text() for page in pdf)
            page_count = pdf.page_count
    except DocumentProcessingError:
        raise
    except (pymupdf.FileDataError, ValueError) as exc:
        raise DocumentProcessingError("The PDF could not be read.") from exc

    document_id = uuid4()
    save_filename = Path(file.filename or "document.pdf").name
    document_dir = STORAGE_DIR / str(document_id)

    document = Document(
        id=document_id,
        filename=save_filename,
        page_count=page_count,
        extracted_text=extracted_text,
        created_at=datetime.now(UTC),
    )

    try:
        document_dir.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise DocumentProcessingError(
            "Failed to create a storage directory for the document.", 
            status_code=500,
        ) from exc

    try:
        (document_dir / "original.pdf").write_bytes(content)
        db.add(document)
        db.commit()
    except (OSError, SQLAlchemyError) as exc:
        # Clean up the storage directory if something went wrong.
        db.rollback()
        shutil.rmtree(document_dir, ignore_errors=True)
        raise DocumentProcessingError(
            "Failed to save the document.", 
            status_code=500,
        ) from exc

    return document
