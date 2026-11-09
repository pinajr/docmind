from datetime import date
from decimal import Decimal

from app.schemas.extraction.invoice import InvoiceExtraction


def test_invoice_fields_are_optional():
    invoice = InvoiceExtraction()

    assert invoice.invoice_number is None
    assert invoice.issue_date is None
    assert invoice.total_amount is None


def test_invoice_accepts_dates_and_money():
    invoice = InvoiceExtraction(
        issue_date=date(2026, 11, 9),
        total_amount=Decimal("125.40"),
    )

    assert invoice.issue_date == date(2026, 11, 9)
    assert invoice.total_amount == Decimal("125.40")
    assert isinstance(invoice.total_amount, Decimal)
    