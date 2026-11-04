import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pymupdf
from fastapi import UploadFile

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


def get_document(document_id: str) -> dict:
    """Load stored metadata for a UUID without accepting a path from the caller."""
    try:
        # Parse and normalize the identifier before using it in a filesystem path.
        safe_id = str(UUID(document_id))
    except (ValueError, AttributeError) as exc:
        raise DocumentNotFoundError from exc

    metadata_path = STORAGE_DIR / safe_id / "metadata.json"
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise DocumentNotFoundError from exc


async def _read_pdf_upload(file: UploadFile) -> bytes:
    """Read an upload in bounded chunks so oversized files are rejected early."""
    content = bytearray()
    while chunk := await file.read(CHUNK_SIZE):
        content.extend(chunk)
        if len(content) > MAX_FILE_SIZE:
            raise DocumentProcessingError("PDF must be 20 MB or smaller.", 413)
    return bytes(content)


async def save_and_extract_pdf(file: UploadFile) -> dict:
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

    document_id = str(uuid4())
    created_at = datetime.now(UTC)
    safe_filename = Path(file.filename or "document.pdf").name
    document_dir = STORAGE_DIR / document_id
    document_dir.mkdir(parents=True, exist_ok=False)

    # The original filename is metadata only. Files are stored under a random ID,
    # so a supplied filename cannot choose or escape the storage directory.
    (document_dir / "original.pdf").write_bytes(content)
    metadata = {
        "id": document_id,
        "filename": safe_filename,
        "page_count": page_count,
        "extracted_text": extracted_text,
        "created_at": created_at.isoformat(),
    }
    (document_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    return metadata
