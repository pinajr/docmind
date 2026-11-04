from datetime import datetime

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    page_count: int
    extracted_text: str
    created_at: datetime
