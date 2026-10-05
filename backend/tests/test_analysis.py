import json

import httpx
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.exceptions import LLMProviderError
from app.llm.factory import build_provider
from app.llm.gemini_provider import GeminiProvider
from app.llm.mock_provider import MockProvider
from app.llm.openai_provider import OpenAIProvider
from app.schemas.analysis import AnalysisResult
from tests.pdf_factory import SAMPLE_JOB_DESCRIPTION, SAMPLE_RESUME_LINES

RESUME_TEXT = "\n".join(SAMPLE_RESUME_LINES)


def _section(score: int = 70) -> dict:
    return {"score": score, "summary": "ok", "strengths": [], "gaps": []}


def minimal_result(**overrides) -> dict:
    data = {
        "job_title": "Engineer",
        "overall_score": 72,
        "score_explanation": "Because.",
        "summary": "Summary.",
        "score_breakdown": {"skills": 70, "experience": 70, "education": 70, "projects": 70, "keywords": 70},
        "experience": _section(),
        "education": _section(),
        "projects": _section(),
        "keyword_analysis": {"match_rate": 60, "keywords": []},
    }
    data.update(overrides)
    return data


class TestAnalysisResultSchema:
    def test_minimal_valid(self) -> None:
        result = AnalysisResult.model_validate(minimal_result())
        assert result.overall_score == 72
        assert result.suggestions == []

    @pytest.mark.parametrize(("raw", "expected"), [(150, 100), (-5, 0), ("88", 88), (71.6, 72), ("n/a", 0)])
    def test_scores_are_clamped(self, raw, expected) -> None:
        assert AnalysisResult.model_validate(minimal_result(overall_score=raw)).overall_score == expected

    def test_lists_are_deduplicated_and_cleaned(self) -> None:
        result = AnalysisResult.model_validate(minimal_result(matching_skills=["Python", " python ", "", "SQL"]))
        assert result.matching_skills == ["Python", "SQL"]

    def test_missing_required_field_fails(self) -> None:
        data = minimal_result()
        del data["score_breakdown"]
        with pytest.raises(ValidationError):
            AnalysisResult.model_validate(data)

    def test_invalid_enum_fails(self) -> None:
        data = minimal_result(suggestions=[{"title": "t", "detail": "d", "priority": "urgent"}])
        with pytest.raises(ValidationError):
            AnalysisResult.model_validate(data)

    def test_json_schema_generation(self) -> None:
        schema = AnalysisResult.model_json_schema()
        assert "overall_score" in schema["properties"]
        assert "overall_score" in schema["required"]


class TestMockProvider:
    def test_produces_valid_structured_result(self) -> None:
        result = MockProvider().analyze(RESUME_TEXT, SAMPLE_JOB_DESCRIPTION)
        # Round-trip through JSON to prove the contract is serializable and valid.
        AnalysisResult.model_validate_json(result.model_dump_json())
        assert {"Python", "FastAPI", "PostgreSQL", "Docker"} <= set(result.matching_skills)
        assert {"Kubernetes", "AWS", "Redis"} <= set(result.missing_skills)
        assert result.suggestions and result.improved_bullets and result.interview_questions
        assert result.recommended_projects
        assert result.keyword_analysis.keywords

    def test_score_depends_on_input(self) -> None:
        provider = MockProvider()
        good = provider.analyze(RESUME_TEXT, SAMPLE_JOB_DESCRIPTION).overall_score
        poor = provider.analyze(
            "Experienced pastry chef skilled in baking, decorating cakes and managing kitchen staff daily.",
            SAMPLE_JOB_DESCRIPTION,
        ).overall_score
        assert good > poor

    def test_is_deterministic(self) -> None:
        a = MockProvider().analyze(RESUME_TEXT, SAMPLE_JOB_DESCRIPTION)
        b = MockProvider().analyze(RESUME_TEXT, SAMPLE_JOB_DESCRIPTION)
        assert a == b


def _openai(handler) -> OpenAIProvider:
    provider = OpenAIProvider(api_key="sk-test", base_url="https://example.test/v1", model="m", timeout=5, temperature=0)
    provider._client = httpx.Client(transport=httpx.MockTransport(handler))
    return provider


class TestRemoteProviders:
    def test_openai_success(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Authorization"] == "Bearer sk-test"
            body = json.loads(request.content)
            assert body["response_format"] == {"type": "json_object"}
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(minimal_result())}}]})

        assert _openai(handler).analyze("resume", "jd").overall_score == 72

    def test_openai_fenced_json(self) -> None:
        content = "```json\n" + json.dumps(minimal_result()) + "\n```"
        provider = _openai(lambda r: httpx.Response(200, json={"choices": [{"message": {"content": content}}]}))
        assert provider.analyze("resume", "jd").job_title == "Engineer"

    def test_invalid_json_retries_then_fails(self) -> None:
        calls = {"n": 0}

        def handler(_: httpx.Request) -> httpx.Response:
            calls["n"] += 1
            return httpx.Response(200, json={"choices": [{"message": {"content": "not json"}}]})

        with pytest.raises(LLMProviderError, match="invalid response"):
            _openai(handler).analyze("resume", "jd")
        assert calls["n"] == 2

    @pytest.mark.parametrize(("status", "message"), [(401, "API key"), (429, "rate limit"), (500, "HTTP 500")])
    def test_http_errors_are_mapped(self, status: int, message: str) -> None:
        with pytest.raises(LLMProviderError, match=message):
            _openai(lambda r: httpx.Response(status, json={})).analyze("resume", "jd")

    def test_gemini_success(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["x-goog-api-key"] == "g-key"
            assert "key=" not in str(request.url)
            text = json.dumps(minimal_result(overall_score=55))
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}}]})

        provider = GeminiProvider(api_key="g-key", model="gemini-test", timeout=5, temperature=0)
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        assert provider.analyze("resume", "jd").overall_score == 55


class TestFactory:
    def _settings(self, **kw) -> Settings:
        base = {"openai_api_key": None, "gemini_api_key": None, "_env_file": None}
        return Settings(**{**base, **kw})

    def test_auto_without_keys_uses_mock(self) -> None:
        assert build_provider(self._settings(llm_provider="auto")).name == "mock"

    def test_auto_prefers_openai(self) -> None:
        assert build_provider(self._settings(llm_provider="auto", openai_api_key="k", gemini_api_key="g")).name == "openai"

    def test_auto_uses_gemini(self) -> None:
        assert build_provider(self._settings(llm_provider="auto", gemini_api_key="g")).name == "gemini"

    def test_explicit_provider_without_key_falls_back(self) -> None:
        assert build_provider(self._settings(llm_provider="openai")).name == "mock"

    def test_blank_key_treated_as_missing(self) -> None:
        assert build_provider(self._settings(llm_provider="auto", openai_api_key="   ")).name == "mock"

    def test_api_key_not_exposed_in_repr(self) -> None:
        assert "super-secret" not in repr(self._settings(openai_api_key="super-secret"))
