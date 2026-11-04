from fastapi import FastAPI
from starlette.middleware.body_limit import RequestBodyLimitMiddleware

from app.services.documents import MAX_FILE_SIZE
from app.routes.documents import router as documents_router


app = FastAPI(
    title="DocMind API",
    description="Upload a PDF and retrieve its extracted text.",
    version="0.1.0",
)

app.add_middleware(
    RequestBodyLimitMiddleware,
    max_body_size=MAX_FILE_SIZE + 64 * 1024,  # Allow a little extra for headers and metadata
)

app.include_router(documents_router, prefix="/api")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Report that the API process is running."""
    return {"status": "ok"}
