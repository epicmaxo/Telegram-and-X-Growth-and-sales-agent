from dataclasses import dataclass


@dataclass
class Opportunity:
    community: str
    context: str
    stated_goal: str
    evidence: str
    potential_problem: str
    mentrast_relevance: str
    confidence: float
    recommended_action: str


class OpportunityService:
    def build_opportunity(self, context: str, goal: str, evidence: str) -> Opportunity:
        return Opportunity(
            community="public community",
            context=context,
            stated_goal=goal,
            evidence=evidence,
            potential_problem="unclear learning path",
            mentrast_relevance="high",
            confidence=0.7,
            recommended_action="Ask a discovery question and assess fit",
        )
