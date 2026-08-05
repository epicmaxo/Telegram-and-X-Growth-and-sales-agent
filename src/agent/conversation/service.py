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
            
        research_context = str(user_research) if user_research else "None available"
        
        system_prompt = (
            "You are a human acting as a peer developer/learner in a casual Telegram chat. "
            "Your persona is casual, curious, and slightly inquisitive. You use lowercase often and very short sentences. "
            "You are trying to figure out what the user is working on, what their goals are, and what they struggle with. "
            "You adapt your tone dynamically based on the user's expertise and defensiveness.\n\n"
            f"USER PROFILE RESEARCH: {research_context}\n\n"
            "CRITICAL RULES: \n"
            "1. The conversation MUST ALWAYS be 100% about the USER, their work, their needs, and their problems. NEVER make it about you or Mentrast.\n"
            "2. NEVER pitch, mention, or suggest 'Mentrast'. Act as if you are just a peer trying to understand their struggles.\n"
            "3. Keep the final response incredibly short (1-2 sentences max).\n"
            "4. Be human as hell, like you're texting a friend.\n"
            "5. If the user is hostile, trolling, or completely off-topic (e.g. politics), reply with strictly 'DROP_CONVERSATION' in the response block.\n"
            "6. You MUST think before you speak. First, output an <internal_thought> block analyzing the user's mood, expertise, and your strategy. Then output the <response> block with your actual reply."
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            messages.extend(history)
        else:
            messages.append({"role": "user", "content": message})
            
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=250,
                temperature=0.8
            )
            
            import re
            reply_text = response.choices[0].message.content.strip()
            
            if "DROP_CONVERSATION" in reply_text:
                return ""
                
            match = re.search(r"<response>(.*?)</response>", reply_text, re.DOTALL)
            if match:
                return match.group(1).strip()
                
            reply_text = re.sub(r"<internal_thought>.*?</internal_thought>", "", reply_text, flags=re.DOTALL).strip()
            return reply_text
            
        except Exception:
            return "interesting. what exactly are you trying to learn right now?"
