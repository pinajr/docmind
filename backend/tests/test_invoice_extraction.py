import pytest

from types import SimpleNamespace
from decimal import Decimal
from openai import OpenAIError

from pydantic import SecretStr

from app.services.invoice_extraction import InvoiceExtractionError
from app.schemas.extraction.invoice import InvoiceExtraction
from app.services import invoice_extraction


def test_extract_invoice_uses_structured_output(monkeypatch):
    expected = InvoiceExtraction(
        invoice_number="INV-42",
        total_amount=Decimal("125.40"),
    )
    recorded = {}


    class FakeResponses:
        def parse(self, **kwargs):
            recorded.update(kwargs)
            return SimpleNamespace(output_parsed=expected)

    
    class FakeOpenAI:
        def __init__(self, *, api_key):
            assert api_key == "test-key"
            self.responses = FakeResponses()

    
    monkeypatch.setattr(invoice_extraction, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(
        invoice_extraction.settings,
        "open_api_key",
        SecretStr("test-key"),
    )
    monkeypatch.setattr(
        invoice_extraction.settings,
        "open_model",
        "test-model",
    )

    result = invoice_extraction.extract_invoice("Invoice INV-42, total 125.40")

    assert result == expected
    assert recorded["model"] == "test-model"
    assert recorded["input"] == "Invoice INV-42, total 125.40"
    assert recorded["text_format"] is InvoiceExtraction


def test_extract_invoice_fails_without_api_key(monkeypatch):
    monkeypatch.setattr(invoice_extraction.settings, "open_api_key", None)

    with pytest.raises(InvoiceExtractionError, match="API key is not configured"):
        invoice_extraction.extract_invoice("Some invoice text")


def test_extract_invoice_fails_without_parsed_result(monkeypatch):
    class FakeResponses:
        def parse(self, **kwargs):
            return SimpleNamespace(output_parsed=None)

    
    class FakeOpenAI:
        def __init__(self, *, api_key):
            self.responses = FakeResponses()

    
    monkeypatch.setattr(invoice_extraction, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(
        invoice_extraction.settings,
        "open_api_key",
        SecretStr("test-key"),
    )
    
    with pytest.raises(InvoiceExtractionError, match="no parsed invoice"):
        invoice_extraction.extract_invoice("Some invoice text")


def test_extract_invoice_logs_safe_provider_error_details(monkeypatch, caplog):
    class FakeOpenAIError(OpenAIError):
        status_code = 429
        request_id = "req-test"

    class FakeResponses:
        def parse(self, **kwargs):
            raise FakeOpenAIError("simulated provider failure")

    class FakeOpenAI:
        def __init__(self, *, api_key):
            self.responses = FakeResponses()

    monkeypatch.setattr(invoice_extraction, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(
        invoice_extraction.settings,
        "open_api_key",
        SecretStr("test-secret"),
    )

    with pytest.raises(InvoiceExtractionError) as exc_info:
        invoice_extraction.extract_invoice("sensitive invoice text")

    assert exc_info.value.status_code == 503
    assert "rate limit or account quota reached" in exc_info.value.message
    assert "FakeOpenAIError" in caplog.text
    assert "status=429" in caplog.text
    assert "request_id=req-test" in caplog.text
    assert "test-secret" not in caplog.text
    assert "sensitive invoice text" not in caplog.text
