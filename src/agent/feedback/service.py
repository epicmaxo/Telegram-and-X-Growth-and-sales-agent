from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FeedbackResult:
    feedback_received: bool
    summary: str
    next_action: str


class FeedbackService:
    def evaluate(self, feedback: str) -> FeedbackResult:
        normalized = feedback.lower()
        if "no" in normalized or "not interested" in normalized or "later" in normalized:
            return FeedbackResult(True, "negative feedback", "pause and log the objection")
        if "yes" in normalized or "interested" in normalized or "love" in normalized:
            return FeedbackResult(True, "positive feedback", "continue with a gentle follow-up")
        return FeedbackResult(True, "mixed feedback", "capture the nuance and ask a clarifying question")
