from dataclasses import dataclass


@dataclass
class EvaluationResult:
    understood_correctly: str
    misunderstood: str
    pitch_too_early: bool
    explanation_too_much: bool
    mentrast_relevant: bool
    reason: str


class EvaluationService:
    def evaluate(self, message: str, stage: str) -> EvaluationResult:
        return EvaluationResult(
            understood_correctly="The person's learning friction was captured",
            misunderstood="No strong misread detected",
            pitch_too_early=False,
            explanation_too_much=False,
            mentrast_relevant="youtube" in message.lower() or "learn" in message.lower(),
            reason="The conversation stayed focused on the person's actual learning difficulty",
        )
