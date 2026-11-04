from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.documents import DocumentUploadResponse
from app.services.documents import (
    DocumentNotFoundError,
    DocumentProcessingError,
    get_document,
    save_and_extract_pdf,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF and extract its text",
)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    """Store an uploaded PDF and return its extracted text."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required.")

    try:
        document = await save_and_extract_pdf(file)
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    finally:
        await file.close()

    return document


@router.get(
    "/{document_id}",
    response_model=DocumentUploadResponse,
    summary="Retrieve a document and its extracted text",
)
def retrieve_document(document_id: str) -> DocumentUploadResponse:
    """Return previously stored document metadata and extracted text."""
    try:
        document = get_document(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found.") from exc
    return document
