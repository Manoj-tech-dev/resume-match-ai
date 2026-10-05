"""ORM models.

Uses portable column types only (String/Text/Integer/DateTime/JSON) so the
schema works unchanged on SQLite and PostgreSQL.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class Analysis(Base):
    __tablename__ = "analyses"

    # Random UUIDs (not autoincrement ints) so ids are not enumerable.
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
    resume_filename: Mapped[str] = mapped_column(String(255))
    resume_pages: Mapped[int] = mapped_column(Integer, default=0)
    resume_characters: Mapped[int] = mapped_column(Integer, default=0)
    job_title: Mapped[str] = mapped_column(String(255))
    job_description: Mapped[str] = mapped_column(Text)
    overall_score: Mapped[int] = mapped_column(Integer, index=True)
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    # The full structured AnalysisResult. Raw resume text is intentionally NOT stored.
    result: Mapped[dict] = mapped_column(JSON)
