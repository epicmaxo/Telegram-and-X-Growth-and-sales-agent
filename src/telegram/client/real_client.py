from __future__ import annotations

import os
from typing import Any
import asyncio

from telethon import TelegramClient as TelethonClient


class RealTelegramClient:
    def __init__(self, api_id: str | None = None, api_hash: str | None = None, phone: str | None = None, session_path: str | None = None) -> None:
        self.api_id = int(api_id) if api_id and api_id.isdigit() else None
        self.api_hash = api_hash
        self.phone = phone
        self.session_path = session_path or os.getenv("TELEGRAM_SESSION_PATH", "./sessions/telegram_account")
        self.client: TelethonClient | None = None

    def is_configured(self) -> bool:
        return bool(self.api_id and self.api_hash and self.phone)

    def get_status(self) -> dict[str, Any]:
        return {
            "configured": self.is_configured(),
            "mode": "user-account",
            "session_path": self.session_path,
            "api_id_present": bool(self.api_id),
            "api_hash_present": bool(self.api_hash),
            "phone_present": bool(self.phone),
        }

    async def connect(self) -> dict[str, Any]:
        if not self.is_configured():
            return {"status": "error", "message": "missing credentials"}

        if self.client is None:
            self.client = TelethonClient(self.session_path, self.api_id, self.api_hash)

        if not await self.client.is_connected():
            await self.client.connect()

        if not await self.client.is_user_authorized():
            return {"status": "not_authorized", "message": "Session exists but is not authorized to a Telegram user."}

        return {"status": "connected", "message": "Telegram account is connected."}

    async def send_message(self, chat_id: str, message: str) -> dict[str, Any]:
        connect_status = await self.connect()
        if connect_status.get("status") != "connected":
            return connect_status

        if not self.client:
            return {"status": "error", "message": "Telegram client not initialized"}

        result = await self.client.send_message(chat_id, message)
        return {"status": "sent", "chat_id": str(chat_id), "result": str(result)}

    async def get_chat_history(self, chat_id: str, limit: int = 20) -> dict[str, Any]:
        connect_status = await self.connect()
        if connect_status.get("status") != "connected":
            return connect_status

        if not self.client:
            return {"status": "error", "message": "Telegram client not initialized"}

        messages = await self.client.get_messages(chat_id, limit=limit)
        return {
            "status": "ok",
            "chat_id": chat_id,
            "messages": [{"id": msg.id, "text": msg.text, "date": str(msg.date)} for msg in messages],
        }
