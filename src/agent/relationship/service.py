from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


class RelationshipManager:
    def __init__(self) -> None:
        self.relationships: dict[str, dict[str, Any]] = {}
        self.blocked_terms = ["no thanks", "not interested", "leave me alone", "stop", "do not contact me"]

    def record_interaction(self, user_id: str, channel: str, outcome: str, message: str | None = None) -> dict[str, Any]:
        now = datetime.now()
        entry = self.relationships.get(user_id, {
            "user_id": user_id,
            "channel": channel,
            "status": "active",
            "interaction_count": 0,
            "last_interaction_at": now.isoformat(),
            "cooldown_until": None,
            "flags": [],
        })
        entry["channel"] = channel
        entry["interaction_count"] += 1
        entry["last_interaction_at"] = now.isoformat()
        entry["status"] = "paused" if outcome in {"no", "blocked", "declined"} else "active"
        entry["flags"] = list(dict.fromkeys(entry.get("flags", []) + (["no_response"] if outcome == "no_response" else [])))

        if outcome in {"no", "blocked", "declined"}:
            entry["cooldown_until"] = (now + timedelta(days=30)).isoformat()
            entry["status"] = "blocked"
        elif outcome == "interested":
            entry["cooldown_until"] = (now + timedelta(days=3)).isoformat()
        else:
            entry["cooldown_until"] = (now + timedelta(hours=12)).isoformat()

        self.relationships[user_id] = entry
        return entry

    def should_engage(self, user_id: str, now: datetime | None = None) -> bool:
        now = now or datetime.now()
        entry = self.relationships.get(user_id)
        if not entry:
            return True
        if entry.get("status") == "blocked":
            return False
        cooldown_until = entry.get("cooldown_until")
        if cooldown_until:
            try:
                return now >= datetime.fromisoformat(cooldown_until)
            except ValueError:
                return True
        return True

    def build_persona_reply(self, user_id: str, message: str) -> str:
        lowered = message.lower()
        if any(term in lowered for term in self.blocked_terms):
            self.record_interaction(user_id, channel="telegram", outcome="blocked", message=message)
            return "I’ll leave it there. Thanks for letting me know."
        if "learn" in lowered or "career" in lowered or "skill" in lowered:
            return "That is a fair point. A lot of people learn the wrong way because they chase too much content and not enough structure."
        return "That makes sense. I’m trying to be helpful, not pushy."

    def pick_target(self, candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not candidates:
            return None
        preferred = [c for c in candidates if c.get("fit_score", 0) >= 0.8]
        if preferred:
            return preferred[0]
        return candidates[0]
