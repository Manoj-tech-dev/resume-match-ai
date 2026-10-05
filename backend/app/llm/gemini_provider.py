"""Google Gemini (Generative Language API) provider."""

from __future__ import annotations

from app.llm.base import RemoteLLMProvider

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider(RemoteLLMProvider):
    name = "gemini"

    def __init__(self, *, api_key: str, model: str, timeout: float, temperature: float) -> None:
        super().__init__(model=model, timeout=timeout, temperature=temperature)
        self._api_key = api_key
        self._url = f"{GEMINI_BASE_URL}/models/{model}:generateContent"

    def _complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.post(
            self._url,
            # Header (not query string) so the key never ends up in URL logs.
            headers={"x-goog-api-key": self._api_key},
            json={
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                "generationConfig": {
                    "temperature": self.temperature,
                    "responseMimeType": "application/json",
                },
            },
        )
        response.raise_for_status()
        try:
            parts = response.json()["candidates"][0]["content"]["parts"]
            return "".join(part.get("text", "") for part in parts)
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("Unexpected Gemini response shape") from exc
