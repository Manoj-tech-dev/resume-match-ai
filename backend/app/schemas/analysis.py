"""Pydantic schemas for the analysis domain.

`AnalysisResult` is the strict, structured contract every LLM provider must
produce. Validators are deliberately forgiving on *shape noise* coming from
LLMs (scores out of range, duplicate list items, stray whitespace) while still
guaranteeing that the API always returns the documented structure.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator


def _clamp_score(value: Any) -> int:
    try:
        number = round(float(value))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, number))


def _clean_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    seen: set[str] = set()
    cleaned: list[str] = []
    for item in value:
        text = str(item).strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            cleaned.append(text)
    return cleaned


Score = Annotated[int, BeforeValidator(_clamp_score), Field(ge=0, le=100)]
StrList = Annotated[list[str], BeforeValidator(_clean_str_list)]
Priority = Literal["high", "medium", "low"]


class _Model(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class ScoreBreakdown(_Model):
    skills: Score = Field(description="How well hard skills match the job (0-100).")
    experience: Score = Field(description="Relevance and depth of work experience (0-100).")
    education: Score = Field(description="Relevance of education/certifications (0-100).")
    projects: Score = Field(description="Relevance of projects (0-100).")
    keywords: Score = Field(description="Coverage of important job keywords (0-100).")


class SectionAssessment(_Model):
    score: Score
    summary: str = Field(description="2-3 sentence assessment.")
    strengths: StrList = Field(default_factory=list)
    gaps: StrList = Field(default_factory=list)


class KeywordMatch(_Model):
    keyword: str
    found: bool
    importance: Priority = "medium"
    occurrences: int = Field(default=0, ge=0, description="Times the keyword appears in the resume.")


class KeywordAnalysis(_Model):
    match_rate: Score = Field(description="Percent of important keywords present in the resume.")
    keywords: list[KeywordMatch] = Field(default_factory=list)


class Suggestion(_Model):
    title: str
    detail: str
    priority: Priority = "medium"


class BulletRewrite(_Model):
    original: str
    improved: str


class ProjectRecommendation(_Model):
    title: str
    description: str
    skills: StrList = Field(default_factory=list)


class InterviewQuestion(_Model):
    question: str
    category: Literal["technical", "behavioral", "experience", "gap"] = "technical"
    rationale: str = ""


class AnalysisResult(_Model):
    """Structured output of a resume-vs-job analysis."""

    job_title: str = Field(description="Inferred job title from the job description.")
    overall_score: Score = Field(description="Overall ATS compatibility score (0-100).")
    score_explanation: str = Field(description="Short explanation of why this score was given.")
    summary: str = Field(description="One-paragraph executive summary of the candidate fit.")
    score_breakdown: ScoreBreakdown
    matching_skills: StrList = Field(default_factory=list)
    missing_skills: StrList = Field(default_factory=list)
    relevant_technologies: StrList = Field(default_factory=list)
    experience: SectionAssessment = Field(description="Experience relevance; `gaps` = experience gaps.")
    education: SectionAssessment
    projects: SectionAssessment
    keyword_analysis: KeywordAnalysis
    suggestions: list[Suggestion] = Field(default_factory=list)
    improved_bullets: list[BulletRewrite] = Field(default_factory=list)
    recommended_projects: list[ProjectRecommendation] = Field(default_factory=list)
    interview_questions: list[InterviewQuestion] = Field(default_factory=list)

    @field_validator("job_title")
    @classmethod
    def _truncate_title(cls, v: str) -> str:
        return (v or "Untitled role")[:120]


# ---------------------------------------------------------------------------
# API response models
# ---------------------------------------------------------------------------


class AnalysisSummary(_Model):
    """Lightweight representation used in history listings."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    resume_filename: str
    job_title: str
    overall_score: int
    provider: str

    @field_validator("created_at")
    @classmethod
    def _ensure_utc(cls, v: datetime) -> datetime:
        # SQLite does not persist tz info; values are always stored in UTC.
        return v.replace(tzinfo=UTC) if v.tzinfo is None else v


class AnalysisRecord(AnalysisSummary):
    """Full stored analysis."""

    model: str
    job_description: str
    resume_pages: int
    resume_characters: int
    result: AnalysisResult


class AnalysisListResponse(_Model):
    items: list[AnalysisSummary]
    total: int
    limit: int
    offset: int


class HealthResponse(_Model):
    status: Literal["ok", "degraded"]
    version: str
    environment: str
    database: Literal["ok", "error"]
    llm_provider: str
    llm_model: str
    max_upload_size_mb: float


class ErrorDetail(_Model):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(_Model):
    error: ErrorDetail
