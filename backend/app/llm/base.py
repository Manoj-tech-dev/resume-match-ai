"""LLM provider abstraction.

Every provider returns a validated `AnalysisResult`. Remote providers only have
to implement `_complete()` (send prompt, return raw JSON text); prompt building,
JSON parsing, validation and retry live here once.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod

import httpx
from pydantic import ValidationError

from app.core.exceptions import LLMProviderError
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.schemas.analysis import AnalysisResult

logger = logging.getLogger("app.llm")


class LLMProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def analyze(self, resume_text: str, job_description: str) -> AnalysisResult:
        """Analyze a resume against a job description."""


class RemoteLLMProvider(LLMProvider):
    """Base for HTTP-based providers that return JSON text."""

    max_attempts = 2

    def __init__(self, *, model: str, timeout: float, temperature: float) -> None:
        self.model = model
        self.temperature = temperature
        self._client = httpx.Client(timeout=timeout)

    @abstractmethod
    def _complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send the prompt and return the raw model text (expected to be JSON)."""

    def analyze(self, resume_text: str, job_description: str) -> AnalysisResult:
        user_prompt = build_user_prompt(resume_text, job_description)
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                raw = self._complete(SYSTEM_PROMPT, user_prompt)
                return AnalysisResult.model_validate(_parse_json(raw))
            except (ValueError, ValidationError) as exc:
                # Malformed/incomplete JSON: retrying usually fixes it.
                last_error = exc
                logger.warning("%s returned invalid JSON (attempt %d/%d)", self.name, attempt, self.max_attempts)
            except httpx.TimeoutException as exc:
                raise LLMProviderError("The AI provider timed out. Please try again.") from exc
            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code
                logger.error("%s HTTP error %d", self.name, code)
                if code in (401, 403):
                    raise LLMProviderError("The AI provider rejected the API key. Check your configuration.") from exc
                if code == 429:
                    raise LLMProviderError("The AI provider rate limit was reached. Please try again shortly.") from exc
                raise LLMProviderError(f"The AI provider returned an error (HTTP {code}).") from exc
            except httpx.HTTPError as exc:
                logger.error("%s transport error: %s", self.name, type(exc).__name__)
                raise LLMProviderError("Could not reach the AI provider.") from exc
        raise LLMProviderError("The AI provider returned an invalid response. Please try again.") from last_error


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    # Tolerate ```json fenced output.
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    return data
