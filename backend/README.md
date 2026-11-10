# DocMind

DocMind is a FastAPI backend that stores PDF documents, extracts selectable
text, and uses OpenAI structured outputs to extract invoice fields. Invoice
results are validated with Pydantic and persisted in PostgreSQL.

## Features

- PDF upload with a 20 MB limit and basic PDF validation.
- Selectable-text extraction with PyMuPDF.
- Local storage of the original PDF and PostgreSQL storage of document data.
- On-demand invoice extraction through the OpenAI API.
- Pydantic validation for invoice dates and monetary values.
- Retrieval of saved documents and invoice extraction results.
- Automated tests for API behavior, persistence, and provider failures.

## Requirements

- Python 3.11 or newer.
- [`uv`](https://docs.astral.sh/uv/).
- PostgreSQL.
- An OpenAI API key and access to a model that supports structured outputs to
  run real invoice extraction. The model name is configurable.

## Setup

From the repository root:

```sh
cd backend
uv sync
```

Create `backend/.env` with the PostgreSQL settings and OpenAI configuration:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=docmind
DB_USER=your_database_user
DB_PASSWORD=your_database_password

OPEN_API_KEY=your_openai_api_key
OPEN_MODEL=your_structured_output_model
```

Keep `.env` private; never commit API keys or database passwords. `OPEN_API_KEY`
is optional for starting the API and running the test suite, but required to
request a real extraction. Use a model enabled for your OpenAI account that
supports the SDK's structured-output parsing.

Apply database migrations:

```sh
uv run alembic upgrade head
```

## Run

Start the API from the `backend/` directory:

```sh
uv run uvicorn app.main:app --reload
```

- Interactive API documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

## Try the invoice workflow

1. In Swagger, use `POST /api/documents` to upload a selectable-text PDF. The
   response includes the document ID, extracted text, and metadata.
2. Use `POST /api/documents/{document_id}/extract` with that ID to request
   structured invoice extraction. This makes a real OpenAI API request and may
   incur charges.
3. Use `GET /api/documents/{document_id}` to retrieve the document and its
   persisted `invoice_extraction`.

The invoice response includes invoice number, issue and due dates, supplier and
customer details, subtotal, tax, and total. Fields absent from the source may
be returned as `null`.

## Tests

Run the automated test suite from `backend/`:

```sh
uv run pytest -q
```

The tests use an in-memory SQLite database and mocked OpenAI responses. They do
not require an OpenAI API key, contact OpenAI, or incur API charges.

## Current limitations

- OCR is not implemented. Scanned PDFs without selectable text receive an
  error and must be OCR-processed before invoice extraction.
- Invoice extraction has been checked against one sample invoice; broader
  accuracy evaluation is still needed.
- Original PDFs are stored on the local filesystem. Production deployment
  needs an appropriate shared, access-controlled storage service.
- Authentication, a frontend, document Q&A, comparison, and production
  deployment are not implemented.
