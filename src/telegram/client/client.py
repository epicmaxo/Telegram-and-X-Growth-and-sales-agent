from __future__ import annotations

import os
from typing import Any

try:
    import telethon  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    telethon = None


class TelegramAccountClient:
    def __init__(self, api_id: str | None = None, api_hash: str | None = None, phone: str | None = None) -> None:
        self.api_id = api_id or os.getenv("TELEGRAM_API_ID")
        self.api_hash = api_hash or os.getenv("TELEGRAM_API_HASH")
        self.phone = phone or os.getenv("TELEGRAM_PHONE")
        self.session_path = os.getenv("TELEGRAM_SESSION_PATH", "./sessions/telegram_account")
        self.client = None

    def get_status(self) -> dict[str, Any]:
        missing = []
        if not self.api_id:
            missing.append("api_id")
        if not self.api_hash:
            missing.append("api_hash")
        if not self.phone:
            missing.append("phone")
        return {
            "configured": not missing,
            "missing": missing,
            "session_path": self.session_path,
            "mode": "user-account",
            "telethon_installed": telethon is not None,
        }

    def is_configured(self) -> bool:
        return self.get_status()["configured"]

    def connect(self) -> dict[str, Any]:
        status = self.get_status()
        if not status["configured"]:
            return {"status": "error", "message": "missing credentials", "missing": status["missing"]}

        return {
            "status": "ready",
            "message": "Telegram account client is configured. Use the login flow to create a session.",
            "session_path": self.session_path,
        }

    def send_message(self, chat_id: str, message: str) -> dict[str, Any]:
        if not self.is_configured():
            return {"status": "error", "message": "Telegram account client is not configured"}
        return {"status": "queued", "chat_id": chat_id, "message": message, "mode": "user-account"}

    def get_chat_history(self, chat_id: str, limit: int = 20) -> dict[str, Any]:
        if not self.is_configured():
            return {"status": "error", "message": "Telegram account client is not configured"}
        return {"status": "ready", "chat_id": chat_id, "messages": [], "limit": limit, "mode": "user-account"}
