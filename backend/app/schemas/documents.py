from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.schemas.extraction.invoice import InvoiceExtraction


class DocumentUploadResponse(BaseModel):
    id: UUID
    filename: str
    page_count: int
    extracted_text: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    invoice_extraction: InvoiceExtraction | None = None
