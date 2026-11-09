from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InvoiceExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invoice_number: str | None = Field(
        default=None,
        description="Invoice identifier as written. Null if not present.",
    )

    issue_date: date | None = Field(
        default=None,
        description="Invoice issue date. Null if not present.",
    )
    due_date: date | None = Field(
        default=None,
        description="Payment due date. Null if not present.",
    )

    supplier_name: str | None = Field(
        default=None,
        description="Supplier name. Null if not present.",
    )
    supplier_tax_id: str | None = Field(
        default=None,
        description="Supplier tax identifier. Null if not present.",
    )

    customer_name: str | None = Field(
        default=None,
        description="Customer name. Null if not present.",
    )
    customer_tax_id: str | None = Field(
        default=None,
        description="Customer tax identifier. Null if not present.",
    )

    subtotal: Decimal | None = Field(
        default=None,
        allow_inf_nan=False,
        description="Invoice subtotal as stated. Null if not present.",
    )
    tax_amount: Decimal | None = Field(
        default=None,
        allow_inf_nan=False,
        description="Total tax amount as stated. Null if not present.",
    )
    total_amount: Decimal | None = Field(
        default=None,
        allow_inf_nan=False,
        description="Invoice total as stated. Null if not present.",
    )
