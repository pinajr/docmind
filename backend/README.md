# DocMind backend

This is the first Phase 1 milestone from the project brief: upload a PDF, extract
its selectable text, store the original file and metadata, and retrieve the
result later. Scanned PDFs need OCR, which is planned for a later phase.

## Run locally

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API page.

## Try it

Use `POST /api/documents` with a PDF file in the `file` field. The response
includes a document ID, page count, and extracted text. Use that ID with
`GET /api/documents/{document_id}` to retrieve the saved result. Documents are
stored in `backend/storage/` and that local data directory is ignored by Git.

This local-storage implementation is for the foundation milestone. PostgreSQL
and Alembic are the next infrastructure pieces in Phase 1; they should replace
the JSON metadata files when we move persistence into the database.
