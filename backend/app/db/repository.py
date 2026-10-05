"""Data-access layer for analyses. The rest of the app never touches SQL directly."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Analysis


class AnalysisRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, **fields: object) -> Analysis:
        analysis = Analysis(**fields)
        self._session.add(analysis)
        self._session.commit()
        self._session.refresh(analysis)
        return analysis

    def get(self, analysis_id: str) -> Analysis | None:
        return self._session.get(Analysis, analysis_id)

    def list(self, *, limit: int = 50, offset: int = 0) -> list[Analysis]:
        stmt = (
            select(Analysis)
            .order_by(Analysis.created_at.desc(), Analysis.id)
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt))

    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(Analysis)) or 0

    def delete(self, analysis_id: str) -> bool:
        analysis = self.get(analysis_id)
        if analysis is None:
            return False
        self._session.delete(analysis)
        self._session.commit()
        return True
