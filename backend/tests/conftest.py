from __future__ import annotations

import os

# Ensure importing `app.main` never touches a real DB or external AI provider.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ["LLM_PROVIDER"] = "mock"
os.environ["APP_ENV"] = "test"

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.db.session import Database  # noqa: E402
from app.llm.mock_provider import MockProvider  # noqa: E402
from app.main import create_app  # noqa: E402
from tests.pdf_factory import SAMPLE_JOB_DESCRIPTION, SAMPLE_RESUME_LINES, make_pdf  # noqa: E402


@pytest.fixture
def settings() -> Settings:
    return Settings(database_url="sqlite://", llm_provider="mock", app_env="test", max_upload_size_mb=1, _env_file=None)


@pytest.fixture
def database(settings: Settings) -> Iterator[Database]:
    db = Database(settings.database_url)
    db.create_all()
    yield db
    db.dispose()


@pytest.fixture
def client(settings: Settings, database: Database) -> Iterator[TestClient]:
    app = create_app(settings, database=database, provider=MockProvider())
    with TestClient(app) as c:
        yield c


@pytest.fixture
def resume_pdf() -> bytes:
    return make_pdf(SAMPLE_RESUME_LINES)


@pytest.fixture
def job_description() -> str:
    return SAMPLE_JOB_DESCRIPTION
