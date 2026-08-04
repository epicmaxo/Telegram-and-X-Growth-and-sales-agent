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

    def draft_response(self, message: str, stage: str = "", history: list[dict[str, str]] = None) -> str:
        import os
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "yeah that makes sense. what are you currently working on?"

        client = OpenAI(api_key=api_key)
        
        system_prompt = (
            "You are a human acting as a peer developer/learner in a casual Telegram chat. "
            "Your persona is casual, curious, and slightly inquisitive. You use lowercase often and very short sentences. "
            "You are trying to figure out what the user is working on, what their goals are, and what they struggle with. "
            "CRITICAL RULES: \n"
            "1. NEVER pitch or mention 'Mentrast' immediately. \n"
            "2. Keep it incredibly short (1-2 sentences max).\n"
            "3. Always end with a natural question about THEM, their work, or their learning process.\n"
            "4. Be human as hell, like you're texting a friend. Don't be robotic or overly helpful."
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            messages.extend(history)
        else:
            messages.append({"role": "user", "content": message})
            
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=150,
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "interesting. what exactly are you trying to learn right now?"
