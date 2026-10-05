"""Database engine / session management.

Everything is driven by `DATABASE_URL`, so switching from SQLite to PostgreSQL
only requires installing a driver (e.g. `psycopg`) and changing the URL.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import BACKEND_DIR
from app.db.base import Base


def _resolve_sqlite_url(url: str) -> str:
    """Make relative SQLite paths relative to the backend dir and ensure the folder exists."""
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite" or not parsed.database or parsed.database == ":memory:":
        return url
    db_path = Path(parsed.database)
    if not db_path.is_absolute():
        db_path = (BACKEND_DIR / db_path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return parsed.set(database=str(db_path)).render_as_string(hide_password=False)


class Database:
    def __init__(self, url: str) -> None:
        url = _resolve_sqlite_url(url)
        is_sqlite = make_url(url).get_backend_name() == "sqlite"
        kwargs: dict = {"pool_pre_ping": True}
        if is_sqlite:
            # FastAPI runs sync endpoints in a threadpool.
            kwargs["connect_args"] = {"check_same_thread": False}
            if ":memory:" in url or url.endswith("sqlite://"):
                kwargs["poolclass"] = StaticPool
        self.engine: Engine = create_engine(url, **kwargs)
        if is_sqlite:
            event.listen(self.engine, "connect", _sqlite_pragmas)
        self._session_factory = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)

    def create_all(self) -> None:
        # Import models so they are registered on the metadata.
        from app.db import models  # noqa: F401

        Base.metadata.create_all(self.engine)

    def session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
        finally:
            session.close()

    def ping(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:  # pragma: no cover - depends on infra failure
            return False

    def dispose(self) -> None:
        self.engine.dispose()


def _sqlite_pragmas(dbapi_connection, _record) -> None:  # type: ignore[no-untyped-def]
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()
