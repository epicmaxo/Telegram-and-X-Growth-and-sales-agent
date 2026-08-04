class DiscoveryService:
    def discover_opportunities(self, query: str) -> list[dict[str, object]]:
        return [
            {
                "community": "learning-focused groups",
                "context": query,
                "stated_goal": "find a direction",
                "evidence": "the topic suggests a learning or career challenge",
                "potential_problem": "unclear path",
                "mentrast_relevance": "high",
                "confidence": 0.65,
                "recommended_action": "review and prepare a discovery message",
            }
        ]
