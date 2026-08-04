from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class AnalysisResult:
    goal: str
    current_learning_method: str
    stated_problem: str
    mentrast_fit: str
    conversation_stage: str
    recommended_action: str
    confidence: float = 0.8


class ConversationService:
    def analyze_message(self, message: str) -> AnalysisResult:
        lowered = message.lower()

        if "software engineer" in lowered or "become a" in lowered:
            goal = "become a software engineer"
        elif "data scientist" in lowered:
            goal = "become a data scientist"
        else:
            goal = "discover their goal"

        learning_method = ""
        if "youtube" in lowered:
            learning_method = "YouTube"
        if "tutorial" in lowered or "courses" in lowered:
            learning_method = "YouTube and random tutorials"
        if not learning_method:
            learning_method = "self-directed learning"

        if "don't know where to start" in lowered or "don't know what to learn next" in lowered or "lost" in lowered:
            problem = "I don't know where to start"
        elif "overwhelmed" in lowered:
            problem = "I feel overwhelmed"
        else:
            problem = "unclear path"

        fit = "high" if "lost" in lowered or "don't know where to start" in lowered or "don't know what to learn next" in lowered else "medium"
        stage = "GOAL_DISCOVERY"
        action = "Ask what they want to become and how they currently learn"

        return AnalysisResult(
            goal=goal,
            current_learning_method=learning_method,
            stated_problem=problem,
            mentrast_fit=fit,
            conversation_stage=stage,
            recommended_action=action,
        )

    def draft_response(self, message: str, stage: str) -> str:
        lowered = message.lower()

        if "youtube" in lowered:
            if "don't know what to learn next" in lowered or "don't know where to start" in lowered or "lost" in lowered:
                return (
                    "That makes sense, especially with YouTube. I know it can feel noisy and confusing. "
                    "Mentrast helps turn that into a clearer path, so you can focus on what to learn next."
                )
            return (
                "That is a common way to start. I think the hard part is usually finding direction, not just more content. "
                "Mentrast is built to make that part feel easier."
            )

        if stage == "PROBLEM_DISCOVERY":
            if "overwhelmed" in lowered or "confusing" in lowered:
                return (
                    "That sounds really overwhelming. I know it can feel like too much advice and not enough direction, especially when you are overwhelmed. "
                    "Mentrast helps turn a goal into a simple path forward."
                )
            return (
                "That makes sense. A lot of people want a clearer path, not just more ideas. "
                "Mentrast is meant to help with that."
            )

        return (
            "Thanks for sharing that. I think the real issue is usually getting from interest to a clear next step. "
            "Mentrast is built to help with that in a simple, practical way."
        )
