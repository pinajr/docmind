from fastapi import FastAPI

from app.routes.documents import router as documents_router

app = FastAPI(
    title="DocMind API",
    description="Upload a PDF and retrieve its extracted text.",
    version="0.1.0",
)

app.include_router(documents_router, prefix="/api")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Report that the API process is running."""
    return {"status": "ok"}
