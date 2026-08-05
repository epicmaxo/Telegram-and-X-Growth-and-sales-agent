from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from src.mentrast.knowledge.product import MentrastKnowledge


class ContentGuardrails:
    def __init__(self) -> None:
        self.brand_voice = "simple, calm, direct, and human"
        self.allowed_tone = ["curious", "practical", "encouraging"]
        self.truth_rules = [
            "Never fabricate claims or fake social proof.",
            "Prefer concrete, observable facts over hype.",
            "Stay neutral on sensitive topics and avoid bias.",
        ]
        self.edtech_topics = [
            "learning",
            "skills",
            "career paths",
            "education",
            "productivity",
            "self-directed learning",
            "career growth",
        ]

    def validate_post(self, text: str) -> tuple[bool, str]:
        lowered = text.lower()
        if any(word in lowered for word in ["guaranteed", "best ever", "everyone should"]):
            return False, "Avoid hype and absolute claims"
        if len(text.split()) > 280:
            return False, "Keep the post concise"
        return True, "ok"

    def build_domain_post(self, topic: str, audience: str) -> str:
        return (
            f"People are trying to {topic} without a clear path. "
            f"For {audience}, the real win is simpler focus and a practical next step."
        )

    def build_conversion_post(self, topic: str, audience: str) -> str:
        return (
            f"People want to {topic} but feel stuck. Mentrast gives {audience} a simple path from interest to action."
        )

    def build_reply(self, original_post: str, audience: str) -> str:
        lowered = original_post.lower()
        if any(word in lowered for word in self.edtech_topics):
            return (
                f"That is a fair point. The challenge is often turning interest into a practical next step. "
                f"For {audience}, that usually means clearer structure, less noise, and better focus."
            )
        return (
            f"That is a fair point. The real challenge is often getting from curiosity to a clear next step. "
            f"Mentrast helps {audience} make that path feel much easier."
        )

    def suggest_image_sources(self, topic: str) -> list[str]:
        return [
            f"Use a real photo from a {topic} community, workshop, or study session.",
            "Use a short screen recording of a clean learning workflow or planning board.",
            "Use a branded snapshot from your own product demo, onboarding flow, or content capture.",
            "Avoid generic stock imagery when possible.",
        ]


class OutboundCampaignService:
    def __init__(self, database_service: Any | None = None) -> None:
        self.database_service = database_service
        self.knowledge = MentrastKnowledge()
        self.guardrails = ContentGuardrails()
        self.new_user_daily_cap = 50
        self.follow_up_daily_cap = 100
        self.allowed_start_hour = 9
        self.allowed_end_hour = 21
        self.cooldown_minutes = 30
        self.follow_up_after_hours = 24

    def _is_allowed_time(self, now: datetime) -> bool:
        return self.allowed_start_hour <= now.hour < self.allowed_end_hour

    def _build_message(self, lead: dict[str, Any]) -> str:
        name = lead.get("name", "there")
        if lead.get("is_new", True):
            return f"Hey {name}, quick question - are you currently learning any new tech skills?"
        else:
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
                return f"hey {name}, just bubbling this up. you still looking into learning new skills?"
                
            prompt = (
                f"You are following up with a Telegram user named {name} who hasn't replied to your previous message. "
                "Write a very short (1 sentence max), extremely casual follow-up message trying to bump the conversation. "
                "Do NOT be salesy or pushy. Use lowercase often. Act like a peer who just remembered to check in."
            )
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=60,
                    temperature=0.8
                )
                return response.choices[0].message.content.strip()
            except Exception:
                return f"hey {name}, just bubbling this up. you still looking into learning new skills?"

    def build_social_post(self, topic: str, audience: str) -> str:
        post = self.guardrails.build_domain_post(topic=topic, audience=audience)
        valid, _ = self.guardrails.validate_post(post)
        return post if valid else self.guardrails.build_domain_post(topic="learn a new skill", audience="people who feel stuck")

    def build_social_reply(self, original_post: str, audience: str) -> str:
        reply = self.guardrails.build_reply(original_post, audience)
        valid, _ = self.guardrails.validate_post(reply)
        return reply if valid else self.guardrails.build_reply("that is a fair point", audience)

    def build_brand_post(self, topic: str, audience: str) -> str:
        post = self.guardrails.build_conversion_post(topic=topic, audience=audience)
        valid, _ = self.guardrails.validate_post(post)
        return post if valid else self.guardrails.build_conversion_post(topic="learn a new skill", audience="people who feel stuck")

    def suggest_image_strategy(self, topic: str) -> list[str]:
        return self.guardrails.suggest_image_sources(topic=topic)

    def build_daily_content_plan(self, audience: str = "global learners") -> dict[str, Any]:
        return {
            "reply_posts": 100,
            "direct_posts": 10,
            "reply_theme": "edtech and practical learning conversations",
            "direct_theme": "clearer paths for learning and career growth",
            "reply_example": self.build_social_reply("Education should feel less chaotic and more practical", audience),
            "direct_example": self.build_brand_post(topic="learn a new skill", audience=audience),
        }

    def start_daily_cycle(self, audience: str = "global learners") -> dict[str, Any]:
        plan = self.build_daily_content_plan(audience=audience)
        self._daily_cycle = {
            "status": "started",
            "reply_posts_limit": plan["reply_posts"],
            "direct_posts_limit": plan["direct_posts"],
            "reply_posts_remaining": plan["reply_posts"],
            "direct_posts_remaining": plan["direct_posts"],
            "started_at": datetime.now().isoformat(),
        }
        return self._daily_cycle

    def dispatch_activity(self, activity_type: str, audience: str = "global learners") -> dict[str, Any]:
        if not getattr(self, "_daily_cycle", None):
            self.start_daily_cycle(audience=audience)

        cycle = self._daily_cycle
        if activity_type == "reply":
            if cycle["reply_posts_remaining"] <= 0:
                return {"status": "blocked", "reason": "reply_cap_reached"}
            cycle["reply_posts_remaining"] -= 1
            return {"status": "queued", "activity": "reply", "remaining": cycle["reply_posts_remaining"]}

        if activity_type == "direct":
            if cycle["direct_posts_remaining"] <= 0:
                return {"status": "blocked", "reason": "direct_cap_reached"}
            cycle["direct_posts_remaining"] -= 1
            return {"status": "queued", "activity": "direct", "remaining": cycle["direct_posts_remaining"]}

        return {"status": "error", "reason": "unknown_activity"}

    def run_batch(self, leads: list[dict[str, Any]], now: datetime | None = None, dry_run: bool = False) -> dict[str, Any]:
        now = now or datetime.now()
        # Time window check removed: if a user is online, they can be messaged regardless of the local server time.

        queued: list[dict[str, Any]] = []
        sent_count = 0
        skipped = 0
        new_count = 0
        follow_up_count = 0

        for lead in leads:
            name = lead.get("name", "lead")
            is_new = lead.get("is_new", True)
            last_sent_at = lead.get("last_sent_at")
            if isinstance(last_sent_at, str):
                last_sent_at = datetime.fromisoformat(last_sent_at)
            is_on_cooldown = False
            if isinstance(last_sent_at, datetime):
                if is_new:
                    is_on_cooldown = now - last_sent_at < timedelta(minutes=self.cooldown_minutes)
                else:
                    is_on_cooldown = now - last_sent_at < timedelta(hours=self.follow_up_after_hours)

            if is_on_cooldown:
                skipped += 1
                continue

            if is_new:
                if new_count >= self.new_user_daily_cap:
                    skipped += 1
                    continue
                new_count += 1
            else:
                if follow_up_count >= self.follow_up_daily_cap:
                    skipped += 1
                    continue
                follow_up_count += 1

            if not dry_run and not lead.get("chat_id"):
                skipped += 1
                continue

            lead["last_sent_at"] = now
            queued.append({
                "lead": lead,
                "message": self._build_message(lead),
                "is_new": is_new,
                "conversation_id": f"outreach-{name}",
                "chat_id": lead.get("chat_id"),
            })
            sent_count += 1

        return {
            "sent_count": sent_count,
            "queued_messages": queued,
            "skipped_count": skipped,
            "reason": "ok" if sent_count else "cooldown",
            "new_user_count": new_count,
            "follow_up_count": follow_up_count,
            "new_user_daily_cap": self.new_user_daily_cap,
            "follow_up_daily_cap": self.follow_up_daily_cap,
        }
