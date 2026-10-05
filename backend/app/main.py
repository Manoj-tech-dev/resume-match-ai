"""FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analyses, health
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db.session import Database
from app.llm.base import LLMProvider
from app.llm.factory import build_provider

logger = logging.getLogger("app")


def create_app(
    settings: Settings | None = None,
    *,
    database: Database | None = None,
    provider: LLMProvider | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    db = database or Database(settings.database_url)
    db.create_all()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger.info("%s v%s starting (env=%s)", settings.app_name, settings.app_version, settings.app_env)
        yield
        db.dispose()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Analyze PDF resumes against job descriptions with structured, AI-generated feedback.",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    app.state.settings = settings
    app.state.db = db
    app.state.llm_provider = provider or build_provider(settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(health.router, prefix="/api")
    app.include_router(analyses.router, prefix="/api")
    return app


app = create_app()
