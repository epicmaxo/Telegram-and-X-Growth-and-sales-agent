from __future__ import annotations

import os
from typing import Any
import asyncio

from telethon import TelegramClient as TelethonClient
from telethon.sessions import StringSession

class RealTelegramClient:
    def __init__(self, api_id: str | None = None, api_hash: str | None = None, phone: str | None = None, session_path: str | None = None, database_service: Any = None) -> None:
        self.api_id = int(api_id) if api_id and api_id.isdigit() else None
        self.api_hash = api_hash
        self.phone = phone
        self.database_service = database_service
        self.client: TelethonClient | None = None

    def _load_session_string(self) -> str | None:
        if self.database_service:
            try:
                user = self.database_service.get_admin_user()
                if user.telegram_session_string:
                    return user.telegram_session_string
            except Exception:
                pass
        return os.getenv("TELEGRAM_SESSION_STRING")

    def is_configured(self) -> bool:
        return bool(self.api_id and self.api_hash and self.phone)

    def get_status(self) -> dict[str, Any]:
        return {
            "configured": self.is_configured(),
            "mode": "user-account",
            "session_string_present": bool(self._load_session_string()),
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
            self.client = TelethonClient(StringSession(self._load_session_string() or ""), self.api_id, self.api_hash)

        if not self.client.is_connected():
            await self.client.connect()

        if not await self.client.is_user_authorized():
            return {"status": "not_authorized", "message": "Session exists but is not authorized to a Telegram user."}

        self._register_message_handler()

        return {"status": "connected", "message": "Telegram account is connected."}

    def _register_message_handler(self):
        from telethon import events
        
        if getattr(self, '_handler_registered', False):
            return
            
        @self.client.on(events.NewMessage(incoming=True))
        async def handle_new_message(event):
            if event.is_private:
                from src.main import conversation_service, relationship_manager
                user = await event.get_sender()
                if not user or getattr(user, 'bot', False):
                    return
                    
                user_id = str(user.id)
                # Only auto-reply to users we have previously tracked in our leads DB
                if user_id not in relationship_manager.relationships:
                    return
                    
                if not relationship_manager.should_engage(user_id):
                    return
                
                relationship_manager.record_interaction(user_id, channel="telegram", outcome="active", message=event.raw_text)
                analysis = conversation_service.analyze_message(event.raw_text)
                reply = conversation_service.draft_response(event.raw_text, stage=analysis.conversation_stage)
                
                if reply:
                    await self.client.send_message(user_id, reply)
                    relationship_manager.record_interaction(user_id, channel="telegram", outcome="active", message=reply)

        self._handler_registered = True

    async def send_code_request(self) -> dict[str, Any]:
        if not self.is_configured():
            missing = []
            if not self.api_id: missing.append("TELEGRAM_API_ID")
            if not self.api_hash: missing.append("TELEGRAM_API_HASH")
            if not self.phone: missing.append("TELEGRAM_PHONE")
            return {"status": "error", "message": f"Missing credentials in Render: {', '.join(missing)}"}
            
        try:
            if self.client is None:
                self.client = TelethonClient(StringSession(self._load_session_string() or ""), self.api_id, self.api_hash)
                
            if not self.client.is_connected():
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
            if not self.client.is_connected():
                await self.client.connect()
                
            await self.client.sign_in(self.phone, code)
            new_session_string = self.client.session.save()
            if self.database_service:
                try:
                    self.database_service.update_telegram_session(new_session_string)
                except Exception:
                    pass
            return {"status": "connected", "message": "Successfully signed in", "session_string": new_session_string}
        except Exception as e:
            return {"status": "error", "message": f"Telegram Error: {str(e)}"}

    async def search_and_join_groups(self, query: str, limit: int = 5) -> dict[str, Any]:
        connect_status = await self.connect()
        if connect_status.get("status") != "connected":
            return connect_status
            
        from telethon.tl.functions.contacts import SearchRequest
        from telethon.tl.functions.channels import JoinChannelRequest
        
        try:
            joined = []
            failed = []
            found = []
            
            # Telegram's API doesn't support long sentence searches.
            # We must split the query into individual keywords and search them one by one.
            keywords = [k.strip() for k in query.split() if k.strip()]
            if not keywords:
                keywords = ["tech"]

            for keyword in keywords:
                result = await self.client(SearchRequest(q=keyword, limit=limit))
                
                for chat in result.chats:
                    is_megagroup = getattr(chat, 'megagroup', False)
                    is_broadcast = getattr(chat, 'broadcast', False)
                    
                    found.append({
                        "id": getattr(chat, 'id', None), 
                        "title": getattr(chat, 'title', None), 
                        "type": type(chat).__name__,
                        "megagroup": is_megagroup,
                        "broadcast": is_broadcast
                    })
                    
                    # Strictly ONLY join supergroups (megagroups). Basic chats cannot be joined via Search,
                    # and we must explicitly avoid broadcast channels.
                    if is_megagroup and not is_broadcast:
                        try:
                            await self.client(JoinChannelRequest(chat))
                            joined.append({"id": chat.id, "title": chat.title, "username": getattr(chat, 'username', None)})
                        except Exception as e:
                            failed.append({"title": getattr(chat, 'title', 'Unknown'), "error": str(e)})
                        
            return {
                "status": "success", 
                "query": query, 
                "found_chats_count": len(found),
                "found_chats_debug": found,
                "joined_groups": joined,
                "failed_joins": failed
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def extract_active_users(self, chat_id: str, limit: int = 100) -> dict[str, Any]:
        connect_status = await self.connect()
        if connect_status.get("status") != "connected":
            return connect_status
            
        try:
            target_chat = int(chat_id) if chat_id.lstrip('-').isdigit() else chat_id
            # Get recent messages to find active users
            messages = await self.client.get_messages(target_chat, limit=limit)
            active_users = {}
            
            from telethon.tl.types import UserStatusOnline, UserStatusRecently
            
            for msg in messages:
                if msg.sender_id and not getattr(msg.sender, 'bot', False):
                    user = msg.sender
                    
                    # Check if user is online or recently online
                    status = getattr(user, 'status', None)
                    is_active = isinstance(status, (UserStatusOnline, UserStatusRecently))
                    
                    if not is_active:
                        continue
                        
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

        target_chat = int(chat_id) if chat_id.lstrip('-').isdigit() else chat_id
        result = await self.client.send_message(target_chat, message)
        return {"status": "sent", "chat_id": str(chat_id), "result": str(result)}

    async def get_chat_history(self, chat_id: str, limit: int = 20) -> dict[str, Any]:
        connect_status = await self.connect()
        if connect_status.get("status") != "connected":
            return connect_status

        if not self.client:
            return {"status": "error", "message": "Telegram client not initialized"}

        target_chat = int(chat_id) if chat_id.lstrip('-').isdigit() else chat_id
        messages = await self.client.get_messages(target_chat, limit=limit)
        return {
            "status": "ok",
            "chat_id": chat_id,
            "messages": [{"id": msg.id, "text": msg.text, "date": str(msg.date)} for msg in messages],
        }

    async def get_joined_groups(self, limit: int = 50) -> dict[str, Any]:
        connect_status = await self.connect()
        if connect_status.get("status") != "connected":
            return connect_status
            
        try:
            groups = []
            async for dialog in self.client.iter_dialogs(limit=limit):
                entity = dialog.entity
                if dialog.is_group or getattr(entity, 'megagroup', False):
                    groups.append({
                        "id": str(dialog.id),
                        "title": dialog.title
                    })
            return {"status": "success", "groups": groups}
        except Exception as e:
            return {"status": "error", "message": str(e)}

