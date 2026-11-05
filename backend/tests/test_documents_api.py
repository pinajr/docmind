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
