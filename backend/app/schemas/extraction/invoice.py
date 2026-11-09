from pydantic import BaseModel
from decimal import Decimal
from datetime import date


class InvoiceExtraction(BaseModel):
    invoice_number: str | None = None

    issue_date: date | None = None
    due_date: date | None = None

    supplier_name: str | None = None
    supplier_tax_id: str | None = None

    customer_name: str | None = None
    customer_tax_id: str | None = None

    subtotal: Decimal | None = None
    tax_amount: Decimal | None = None
    total_amount: Decimal | None = None
