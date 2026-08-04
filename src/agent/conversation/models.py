from dataclasses import dataclass


@dataclass
class ConversationAnalysis:
    goal: str
    currentSituation: str
    currentLearningMethod: str
    statedProblem: str
    knownFacts: list[str]
    unknowns: list[str]
    possibleFriction: list[str]
    mentrastFit: str
    confidence: float
    conversationStage: str
    recommendedAction: str
    reason: str
