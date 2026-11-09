from decimal import Decimal

from app.routes import documents as document_routes
from app.schemas.extraction.invoice import InvoiceExtraction
from app.services.invoice_extraction import InvoiceExtractionError


def test_upload_rejects_non_pdf_content(client):
    response = client.post(
        "/api/documents",
        files={
            "file": (
                "fake.pdf",
                b"This is not a PDF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "The uploaded file is not a valid PDF."
    }


def test_upload_pdf(client, valid_pdf):
    upload_response = client.post(
        "/api/documents",
        files={
            "file": (
                "sample.pdf",
                valid_pdf,
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 201

    uploaded_document = upload_response.json()
    assert uploaded_document["filename"] == "sample.pdf"
    assert uploaded_document["page_count"] == 1
    assert "DocMind test invoice" in uploaded_document["extracted_text"]


def test_retrieve_uploaded_pdf(client, uploaded_document_response):
    uploaded_document = uploaded_document_response.json()

    response = client.get(f"/api/documents/{uploaded_document['id']}")

    assert response.status_code == 200

    retrieved_document = response.json()
    assert retrieved_document["id"] == uploaded_document["id"]
    assert retrieved_document["filename"] == uploaded_document["filename"]
    assert retrieved_document["page_count"] == uploaded_document["page_count"]
    assert retrieved_document["extracted_text"] == uploaded_document["extracted_text"]


def test_upload_stores_original_pdf(tmp_path, valid_pdf, uploaded_document_response):
    assert uploaded_document_response.status_code == 201
    document_id = uploaded_document_response.json()["id"]

    stored_pdf = tmp_path / document_id / "original.pdf"
    assert stored_pdf.read_bytes() == valid_pdf


def test_extract_invoice_and_retrieve_it(client, uploaded_document_response, monkeypatch):
    document_id = uploaded_document_response.json()["id"]

    expected = InvoiceExtraction(
        invoice_number="INV-42",
        total_amount=Decimal("125.40"),
    )


    def fake_extract_invoice(text):
        assert "DocMind test invoice" in text
        return expected


    monkeypatch.setattr(
        document_routes,
        "extract_invoice",
        fake_extract_invoice,
    )

    response = client.post(f"/api/documents/{document_id}/extract")

    assert response.status_code == 200
    assert response.json()["invoice_number"] == "INV-42"
    assert response.json()["total_amount"] == "125.40"

    retrieved = client.get(f"/api/documents/{document_id}")

    assert retrieved.status_code == 200
    assert retrieved.json()["invoice_extraction"]["invoice_number"] == "INV-42"
    assert retrieved.json()["invoice_extraction"]["total_amount"] == "125.40"


def test_extract_invoice_returns_404_for_missing_document(client):
    response = client.post("/api/documents/not-a-uuid/extract")

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found."}


def test_extract_invoice_returns_502_when_provider_fails(
    client,
    uploaded_document_response,
    monkeypatch,
):
    document_id = uploaded_document_response.json()["id"]


    def fake_extract_invoice(text):
        raise InvoiceExtractionError("Provider unavailable")


    monkeypatch.setattr(
        document_routes,
        "extract_invoice",
        fake_extract_invoice,
    )

    response = client.post(f"/api/documents/{document_id}/extract")

    assert response.status_code == 502
    assert response.json() == {"detail": "Invoice extraction failed."}
