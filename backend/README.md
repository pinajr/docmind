# DocMind backend

This is the first Phase 1 milestone from the project brief: upload a PDF, extract
its selectable text, store the original file and metadata, and retrieve the
result later. Scanned PDFs need OCR, which is planned for a later phase.

## Run locally

```sh
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API page.

## Try it

Use `POST /api/documents` with a PDF file in the `file` field. The response
includes a document ID, page count, and extracted text. Use that ID with
`GET /api/documents/{document_id}` to retrieve the saved result. The original
PDF is stored in `backend/storage/`; document metadata and extracted text are
stored in PostgreSQL.

The database connection is configured in `backend/.env`. Apply database
migrations from the `backend/` directory with:

```sh
uv run alembic upgrade head
```
