from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

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


def test_invoice_rejects_unexpected_fields():
    with pytest.raises(ValidationError):
        InvoiceExtraction(unrequested_field="invented value")


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-Infinity"])
def test_invoice_rejects_non_finite_money(amount):
    with pytest.raises(ValidationError):
        InvoiceExtraction(total_amount=Decimal(amount))


def test_invoice_accepts_negative_amount_for_credit_notes():
    invoice = InvoiceExtraction(total_amount=Decimal("-12.50"))

    assert invoice.total_amount == Decimal("-12.50")
    