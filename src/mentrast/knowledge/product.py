from __future__ import annotations


class MentrastKnowledge:
    def __init__(self) -> None:
        self.description = (
            "Mentrast is a Path to Becoming platform. It helps people move from a vague goal to a structured path. "
            "The core idea is that people often know what they want to become but do not know the path between where they are now and where they want to go."
        )

    def get_summary(self) -> str:
        return self.description
