from __future__ import annotations
import re
import time
import logging

logger = logging.getLogger(__name__)

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
    """Service that builds prompts for the Azure OpenAI model and enforces conversation rules.

    The methods `_should_drop` and `_should_mention_mentrast` run **before** any LLM call so the behavior is deterministic.
    """

    # Track which conversation threads have already received a mentrast mention.
    # Key = tuple of first-message hash so different users get separate tracking.
    _mentrast_mentioned: set = set()

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

    def _should_drop(self, message: str) -> bool:
        """Return True if the message indicates disinterest or a request to stop.
        Matches phrases like "not at the moment", "no", "i'm not interested", "stop", etc.
        """
        lowered = message.lower()
        return bool(re.search(r"\b(not at the moment|no thanks|nah|i'm not interested|not interested|stop messaging|leave me alone|i don't want|stop)\b", lowered))

    def _should_mention_mentrast(self, message: str) -> bool:
        """Return True if the user is clearly struggling (tutorial hell, overwhelmed, stuck, confused...)."""
        lowered = message.lower()
        return bool(re.search(r"\b(tutorial hell|overwhelmed|stuck|confused|don't know|can't|cannot)\b", lowered))

    def draft_response(self, message: str, stage: str = "", history: list[dict[str, str]] = None, user_research: dict[str, str] = None) -> str:
        import os
        from openai import OpenAI, AzureOpenAI
        
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        api_key = os.getenv("OPENAI_API_KEY")
        
        if azure_api_key and azure_endpoint:
            client = AzureOpenAI(
                api_key=azure_api_key,
                azure_endpoint=azure_endpoint,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            )
            model_name = azure_deployment or "gpt-4"
        elif api_key:
            client = OpenAI(api_key=api_key)
            model_name = "gpt-4o-mini"
        else:
            return "yeah that makes sense. what are you currently working on?"
        
        # Early rule enforcement – drop if the user is not interested
        if self._should_drop(message):
            return ""

        # Build a conversation fingerprint from the first user message in history
        conv_id = ""
        if history:
            for h in history:
                if h.get("role") == "user":
                    conv_id = h["content"][:80]
                    break
        if not conv_id:
            conv_id = message[:80]

        # Only inject the mentrast hint ONCE per conversation
        already_mentioned = (
            conv_id in self._mentrast_mentioned
            or any("mentrast" in h.get("content", "").lower() for h in (history or []))
        )
        if self._should_mention_mentrast(message) and not already_mentioned:
            self._mentrast_mentioned.add(conv_id)
            # Insert the mentrast hint so the LLM naturally includes it
            message = f"you should check out mentrast.com – it basically fixes that exact problem.\n{message}"
        
        research_context = str(user_research) if user_research else "None available"
        
        system_prompt = (
            "You are a human acting as a peer developer/learner in a casual Telegram chat. "
            "Your persona is casual, curious, and slightly inquisitive. You use lowercase often and very short sentences. "
            "You are trying to figure out what the user is working on, what their goals are, and what they struggle with. "
            "You adapt your tone dynamically based on the user's expertise and defensiveness.\n\n"
            f"USER PROFILE RESEARCH: {research_context}\n\n"
            "CRITICAL RULES: \n"
            "1. Start by focusing 100% on the USER, their work, and their projects. Do NOT mention Mentrast immediately.\n"
            "2. Your ultimate goal is to eventually mention 'mentrast.com' in EVERY conversation. You do not need to wait for them to be frustrated or struggling. Find a natural, conversational moment to bring it up as a helpful tool or recommendation based on what they are working on.\n"
            "3. When mentioning mentrast.com, frame it casually like a friend recommending a tool, NOT a sales pitch. (e.g. 'you should check out mentrast.com, it might be exactly what you need for that').\n"
            "4. IMPORTANT: You must only mention mentrast.com ONCE per conversation. If you have already recommended it, DO NOT mention it again.\n"
            "5. Keep the final response incredibly short (1-2 sentences max).\n"
            "6. Be human as hell, like you're texting a friend.\n"
            "7. If the user says they are not interested, not learning anything, or gives a negative response like 'not at the moment' or 'no', YOU MUST reply with strictly 'DROP_CONVERSATION' in the response block to stop bothering them.\n"
            "8. If the user is hostile, trolling, or completely off-topic (e.g. politics), reply with strictly 'DROP_CONVERSATION' in the response block.\n"
            "9. You MUST think before you speak. First, output an <internal_thought> block analyzing the user's mood, expertise, and whether it is time to drop the link. Then output the <response> block with your actual reply."
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            messages.extend(history)
        else:
            messages.append({"role": "user", "content": message})
            
        # Retry with exponential backoff for rate-limits
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=250,
                    temperature=0.8
                )

                reply_text = response.choices[0].message.content.strip()

                if "DROP_CONVERSATION" in reply_text:
                    return ""

                match = re.search(r"<response>(.*?)</response>", reply_text, re.DOTALL)
                if match:
                    return match.group(1).strip()

                reply_text = re.sub(r"<internal_thought>.*?</internal_thought>", "", reply_text, flags=re.DOTALL).strip()
                return reply_text

            except Exception as exc:
                logger.warning("LLM call attempt %d/%d failed: %s", attempt + 1, max_retries, exc)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt * 5)  # 5s, 10s, 20s backoff
                else:
                    logger.error("All %d LLM retries exhausted.", max_retries)
                    return "interesting. what exactly are you trying to learn right now?"
