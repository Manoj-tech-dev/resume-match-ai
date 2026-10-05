"""Select the configured LLM provider, falling back to the mock provider when no key is set."""

from __future__ import annotations

import logging

from app.core.config import Settings
from app.llm.base import LLMProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.mock_provider import MockProvider
from app.llm.openai_provider import OpenAIProvider

logger = logging.getLogger("app.llm")


def _secret(value) -> str | None:  # type: ignore[no-untyped-def]
    raw = value.get_secret_value().strip() if value is not None else ""
    return raw or None


def build_provider(settings: Settings) -> LLMProvider:
    choice = settings.llm_provider
    openai_key = _secret(settings.openai_api_key)
    gemini_key = _secret(settings.gemini_api_key)
    common = {"timeout": settings.llm_timeout_seconds, "temperature": settings.llm_temperature}

    if choice == "auto":
        choice = "openai" if openai_key else "gemini" if gemini_key else "mock"

    if choice == "openai":
        if openai_key:
            provider: LLMProvider = OpenAIProvider(
                api_key=openai_key, base_url=settings.openai_base_url, model=settings.openai_model, **common
            )
        else:
            logger.warning("LLM_PROVIDER=openai but OPENAI_API_KEY is not set; using mock provider")
            provider = MockProvider()
    elif choice == "gemini":
        if gemini_key:
            provider = GeminiProvider(api_key=gemini_key, model=settings.gemini_model, **common)
        else:
            logger.warning("LLM_PROVIDER=gemini but GEMINI_API_KEY is not set; using mock provider")
            provider = MockProvider()
    else:
        provider = MockProvider()

    logger.info("LLM provider: %s (model=%s)", provider.name, provider.model)
    return provider
