from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_session
from app.schemas.documents import DocumentUploadResponse
from app.services.documents import (
    DocumentNotFoundError,
    DocumentProcessingError,
    get_document,
    save_and_extract_pdf,
)
from app.schemas.extraction.invoice import InvoiceExtraction
from app.services.invoice_extraction import (
    InvoiceExtractionError,
    extract_invoice,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF and extract its text",
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
) -> DocumentUploadResponse:
    """Store an uploaded PDF and return its extracted text."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required.")

    try:
        document = await save_and_extract_pdf(file, db)
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
def retrieve_document(
    document_id: str,
    db: Session = Depends(get_session),
) -> DocumentUploadResponse:
    """Return previously stored document metadata and extracted text."""
    try:
        document = get_document(document_id, db)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found.") from exc
    return document


@router.post(
    "/{document_id}/extract",
    response_model=InvoiceExtraction,
    summary="Extract invoice fields from a saved document",
)
def extract_document_invoice(
    document_id: str,
    db: Session = Depends(get_session),
) -> InvoiceExtraction:
    try:
        document = get_document(document_id, db)
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=404, 
            detail="Document not found.",
        ) from exc

    try:
        invoice = extract_invoice(document.extracted_text)
    except InvoiceExtractionError as exc:
        raise HTTPException(
            status_code=502,
            detail="Invoice extraction failed.",
        ) from exc

    document.invoice_extraction = invoice.model_dump(mode="json")

    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save invoice extraction",
        ) from exc

    return invoice
    