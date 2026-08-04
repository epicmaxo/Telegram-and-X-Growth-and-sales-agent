from __future__ import annotations

from typing import Any

from src.storage.database import DatabaseService


class PersonMemoryService:
    def __init__(self, database_service: DatabaseService | None = None) -> None:
        self.database_service = database_service or DatabaseService()

    def remember(self, conversation_id: str, facts: dict[str, Any]) -> dict[str, Any]:
        conversation = self.database_service.get_conversation(conversation_id)
        if not conversation:
            conversation = self.database_service.create_conversation(conversation_id=conversation_id, state={})

        state = dict(conversation.state or {})
        state.update(facts)
        return {"conversation_id": conversation_id, "memory": state}

    def get_memory(self, conversation_id: str) -> dict[str, Any]:
        conversation = self.database_service.get_conversation(conversation_id)
        if not conversation:
            return {}
        return dict(conversation.state or {})
