"""FastAPI dependency wiring."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.repository import AnalysisRepository
from app.db.session import Database
from app.llm.base import LLMProvider
from app.services.analysis_service import AnalysisService


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_database(request: Request) -> Database:
    return request.app.state.db


def get_session(db: Annotated[Database, Depends(get_database)]) -> Iterator[Session]:
    yield from db.session()


def get_provider(request: Request) -> LLMProvider:
    return request.app.state.llm_provider


def get_analysis_service(
    session: Annotated[Session, Depends(get_session)],
    provider: Annotated[LLMProvider, Depends(get_provider)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> AnalysisService:
    return AnalysisService(AnalysisRepository(session), provider, settings)


AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
DatabaseDep = Annotated[Database, Depends(get_database)]
ProviderDep = Annotated[LLMProvider, Depends(get_provider)]
