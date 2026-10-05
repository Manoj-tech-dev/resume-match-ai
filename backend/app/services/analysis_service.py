"""Orchestrates the resume analysis use case: validate -> extract -> analyze -> persist."""

from __future__ import annotations

import logging
import time

from app.core.config import Settings
from app.core.exceptions import NotFoundError, ValidationFailedError
from app.db.models import Analysis
from app.db.repository import AnalysisRepository
from app.llm.base import LLMProvider
from app.services.pdf_extractor import extract_text_from_pdf, sanitize_filename, validate_pdf_upload

logger = logging.getLogger("app.analysis")


class AnalysisService:
    def __init__(self, repository: AnalysisRepository, provider: LLMProvider, settings: Settings) -> None:
        self._repo = repository
        self._provider = provider
        self._settings = settings

    def validate_job_description(self, job_description: str | None) -> str:
        text = (job_description or "").strip()
        if not text:
            raise ValidationFailedError("Job description is required.")
        if len(text) < self._settings.min_job_description_chars:
            raise ValidationFailedError(
                f"Job description is too short. Please paste at least {self._settings.min_job_description_chars} characters."
            )
        if len(text) > self._settings.max_job_description_chars:
            raise ValidationFailedError(
                f"Job description is too long (max {self._settings.max_job_description_chars:,} characters)."
            )
        return text

    def analyze(
        self, *, filename: str | None, content_type: str | None, data: bytes, job_description: str | None
    ) -> Analysis:
        jd = self.validate_job_description(job_description)
        validate_pdf_upload(filename, content_type, data, self._settings.max_upload_size_bytes)
        resume = extract_text_from_pdf(data, max_pages=self._settings.max_resume_pages)

        started = time.perf_counter()
        result = self._provider.analyze(resume.text, jd)
        # Log only metadata — never resume or job description contents.
        logger.info(
            "Analysis complete provider=%s pages=%d chars=%d score=%d duration_ms=%d",
            self._provider.name,
            resume.page_count,
            len(resume.text),
            result.overall_score,
            (time.perf_counter() - started) * 1000,
        )

        return self._repo.create(
            resume_filename=sanitize_filename(filename),
            resume_pages=resume.page_count,
            resume_characters=len(resume.text),
            job_title=result.job_title,
            job_description=jd,
            overall_score=result.overall_score,
            provider=self._provider.name,
            model=self._provider.model,
            result=result.model_dump(mode="json"),
        )

    def get(self, analysis_id: str) -> Analysis:
        analysis = self._repo.get(analysis_id)
        if analysis is None:
            raise NotFoundError("Analysis not found.")
        return analysis

    def list(self, *, limit: int, offset: int) -> tuple[list[Analysis], int]:
        return self._repo.list(limit=limit, offset=offset), self._repo.count()

    def delete(self, analysis_id: str) -> None:
        if not self._repo.delete(analysis_id):
            raise NotFoundError("Analysis not found.")
