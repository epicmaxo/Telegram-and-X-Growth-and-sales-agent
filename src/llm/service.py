from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMResponse:
    analysis: dict[str, object]


class LLMService:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def generate(self, prompt: str) -> LLMResponse:
        return LLMResponse(
            analysis={
                "prompt": prompt,
                "mode": "mock",
                "note": "Replace this with GPT-4.0 integration when credentials are available.",
            }
        )
