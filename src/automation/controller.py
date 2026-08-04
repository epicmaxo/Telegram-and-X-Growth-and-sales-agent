from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


class AutomationController:
    def __init__(self, sleep_minutes: int = 30, idle_threshold: int = 3) -> None:
        self.sleep_minutes = sleep_minutes
        self.idle_threshold = idle_threshold
        self.state = {
            "status": "idle",
            "telegram": {"connected": False, "awake": False, "last_activity_at": None},
            "x": {"connected": False, "awake": False, "last_activity_at": None},
            "sleep_until": None,
            "idle_checks": 0,
        }

    def mark_channel_activity(self, channel: str, activity: str | None = None) -> dict[str, Any]:
        if channel not in {"telegram", "x"}:
            return {"status": "error", "reason": "unknown_channel"}

        now = datetime.now()
        channel_state = self.state[channel]
        channel_state["connected"] = True
        channel_state["awake"] = True
        channel_state["last_activity_at"] = now.isoformat()
        self.state["status"] = "awake"
        self.state["sleep_until"] = None
        self.state["idle_checks"] = 0
        return {"status": "awake", "channel": channel, "activity": activity or "message"}

    def tick(self) -> dict[str, Any]:
        now = datetime.now()
        sleep_until = self.state.get("sleep_until")
        if sleep_until and now < sleep_until:
            return {"status": "sleeping", "sleep_until": sleep_until.isoformat()}

        if self.state["status"] == "awake":
            self.state["idle_checks"] += 1
            if self.state["idle_checks"] >= self.idle_threshold:
                self.state["status"] = "idle"
                self.state["sleep_until"] = now + timedelta(minutes=self.sleep_minutes)
                return {"status": "sleeping", "sleep_until": self.state["sleep_until"].isoformat()}

        return {"status": self.state["status"], "idle_checks": self.state["idle_checks"]}

    def get_status(self) -> dict[str, Any]:
        return {
            "status": self.state["status"],
            "sleep_minutes": self.sleep_minutes,
            "idle_threshold": self.idle_threshold,
            "telegram": self.state["telegram"],
            "x": self.state["x"],
            "sleep_until": self.state.get("sleep_until"),
            "idle_checks": self.state["idle_checks"],
        }
