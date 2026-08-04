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
        
        # Ensure the parent directory exists to prevent SQLite OperationalError
        parent_dir = os.path.dirname(self.session_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
            
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
            missing = []
            if not self.api_id: missing.append("TELEGRAM_API_ID")
            if not self.api_hash: missing.append("TELEGRAM_API_HASH")
            if not self.phone: missing.append("TELEGRAM_PHONE")
            return {"status": "error", "message": f"Missing credentials in Render: {', '.join(missing)}"}

        if self.client is None:
            self.client = TelethonClient(self.session_path, self.api_id, self.api_hash)

        if not await self.client.is_connected():
            await self.client.connect()

        if not await self.client.is_user_authorized():
            return {"status": "not_authorized", "message": "Session exists but is not authorized to a Telegram user."}

        return {"status": "connected", "message": "Telegram account is connected."}

    async def send_code_request(self) -> dict[str, Any]:
        if not self.is_configured():
            missing = []
            if not self.api_id: missing.append("TELEGRAM_API_ID")
            if not self.api_hash: missing.append("TELEGRAM_API_HASH")
            if not self.phone: missing.append("TELEGRAM_PHONE")
            return {"status": "error", "message": f"Missing credentials in Render: {', '.join(missing)}"}
            
        try:
            if self.client is None:
                self.client = TelethonClient(self.session_path, self.api_id, self.api_hash)
                
            if not await self.client.is_connected():
                await self.client.connect()
                
            result = await self.client.send_code_request(self.phone)
            self.phone_code_hash = result.phone_code_hash
            return {"status": "code_sent", "phone_code_hash": self.phone_code_hash}
        except Exception as e:
            return {"status": "error", "message": f"Telegram Error: {str(e)}"}

    async def sign_in(self, code: str) -> dict[str, Any]:
        if not self.client:
            return {"status": "error", "message": "Client not connected. Request code first."}
            
        try:
            if not await self.client.is_connected():
                await self.client.connect()
                
            await self.client.sign_in(self.phone, code)
            return {"status": "connected", "message": "Successfully signed in"}
        except Exception as e:
            return {"status": "error", "message": f"Telegram Error: {str(e)}"}

    async def search_and_join_groups(self, query: str, limit: int = 5) -> dict[str, Any]:
        connect_status = await self.connect()
        if connect_status.get("status") != "connected":
            return connect_status
            
        from telethon.tl.functions.contacts import SearchRequest
        from telethon.tl.functions.channels import JoinChannelRequest
        
        try:
            # Search for groups
            result = await self.client(SearchRequest(q=query, limit=limit))
            joined = []
            
            for chat in result.chats:
                if getattr(chat, 'megagroup', False) or getattr(chat, 'broadcast', False):
                    try:
                        await self.client(JoinChannelRequest(chat))
                        joined.append({"id": chat.id, "title": chat.title, "username": getattr(chat, 'username', None)})
                    except Exception as e:
                        print(f"Failed to join {chat.title}: {e}")
                        
            return {"status": "success", "query": query, "joined_groups": joined}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def extract_active_users(self, chat_id: str, limit: int = 100) -> dict[str, Any]:
        connect_status = await self.connect()
        if connect_status.get("status") != "connected":
            return connect_status
            
        try:
            # Get recent messages to find active users
            messages = await self.client.get_messages(chat_id, limit=limit)
            active_users = {}
            
            for msg in messages:
                if msg.sender_id and not getattr(msg.sender, 'bot', False):
                    user = msg.sender
                    if user.id not in active_users:
                        active_users[user.id] = {
                            "id": user.id,
                            "username": getattr(user, 'username', None),
                            "first_name": getattr(user, 'first_name', None),
                            "last_name": getattr(user, 'last_name', None),
                            "messages_sent_in_sample": 1
                        }
                    else:
                        active_users[user.id]["messages_sent_in_sample"] += 1
                        
            return {"status": "success", "chat_id": chat_id, "active_users": list(active_users.values())}
        except Exception as e:
            return {"status": "error", "message": str(e)}

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
