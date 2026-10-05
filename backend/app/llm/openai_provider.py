"""OpenAI (and OpenAI-compatible) chat-completions provider."""

from __future__ import annotations

from app.llm.base import RemoteLLMProvider


class OpenAIProvider(RemoteLLMProvider):
    name = "openai"

    def __init__(self, *, api_key: str, base_url: str, model: str, timeout: float, temperature: float) -> None:
        super().__init__(model=model, timeout=timeout, temperature=temperature)
        self._api_key = api_key
        self._url = base_url.rstrip("/") + "/chat/completions"

    def _complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.post(
            self._url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self.model,
                "temperature": self.temperature,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
        )
        response.raise_for_status()
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("Unexpected OpenAI response shape") from exc
