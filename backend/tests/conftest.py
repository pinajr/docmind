from collections.abc import Generator
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def pytest_configure() -> None:
    """Set harmless database settings before the app is imported in tests."""
    os.environ.update(
        {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "docmind_test",
            "DB_USER": "test",
            "DB_PASSWORD": "test",
        }
    )


@pytest.fixture
def client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.database import get_session
    from app.main import app
    from app.models import Document
    from app.services import documents as document_service

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Document.metadata.create_all(bind=test_engine)

    test_session_factory = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    def override_get_session() -> Generator[Session, None, None]:
        with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_session] = override_get_session
    monkeypatch.setattr(document_service, "STORAGE_DIR", tmp_path)

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_session, None)
        Document.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture
def valid_pdf() -> bytes:
    import pymupdf

    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "DocMind test invoice")

        return pdf.tobytes()


@pytest.fixture
def uploaded_document_response(client, valid_pdf):
    return client.post(
        "/api/documents",
        files={
            "file": (
                "sample.pdf",
                valid_pdf,
                "application/pdf",
            )
        },
    )