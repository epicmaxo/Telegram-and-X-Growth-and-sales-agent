from __future__ import annotations

import os
from typing import Any

from src.agent.outreach.service import ContentGuardrails


class XClient:
    def __init__(self, api_key: str | None = None, api_secret: str | None = None, access_token: str | None = None, access_token_secret: str | None = None) -> None:
        self.api_key = api_key or os.getenv("X_API_KEY")
        self.api_secret = api_secret or os.getenv("X_API_SECRET")
        self.access_token = access_token or os.getenv("X_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("X_ACCESS_TOKEN_SECRET")
        self.guardrails = ContentGuardrails()

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret and self.access_token and self.access_token_secret)

    def get_status(self) -> dict[str, Any]:
        return {
            "configured": self.is_configured(),
            "mode": "x",
            "credentials_present": {
                "api_key": bool(self.api_key),
                "api_secret": bool(self.api_secret),
                "access_token": bool(self.access_token),
                "access_token_secret": bool(self.access_token_secret),
            },
            "handle": os.getenv("X_HANDLE"),
            "follower_count": int(os.getenv("X_FOLLOWER_COUNT", "0")) if os.getenv("X_FOLLOWER_COUNT") else None,
        }

    def get_profile_snapshot(self, topic: str = "learning a new skill") -> dict[str, Any]:
        status = self.get_status()
        status["image_recommendations"] = self.guardrails.suggest_image_sources(topic=topic)
        return status

    def _prepare_content(self, text: str) -> str:
        valid, _ = self.guardrails.validate_post(text)
        if valid:
            return text
        return self.guardrails.build_conversion_post(topic="learn a new skill", audience="people who feel stuck")

    async def post_tweet(self, text: str) -> dict[str, Any]:
        if not self.is_configured():
            return {"status": "error", "message": "X credentials are not configured"}
        prepared = self._prepare_content(text)
        return {"status": "queued", "message": prepared, "mode": "x"}

    async def reply_to_post(self, post_id: str, text: str) -> dict[str, Any]:
        if not self.is_configured():
            return {"status": "error", "message": "X credentials are not configured"}
        prepared = self._prepare_content(text)
        return {"status": "queued", "post_id": post_id, "message": prepared, "mode": "x"}
