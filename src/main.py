from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.agent.conversation.service import ConversationService
from src.agent.evaluation.service import EvaluationService
from src.agent.feedback.service import FeedbackService
from src.agent.opportunity.service import OpportunityService
from src.agent.outreach.service import OutboundCampaignService
from src.agent.relationship.service import RelationshipManager
from src.automation.controller import AutomationController
from src.config.settings import Settings
from src.storage.database import DatabaseService
from src.memory.person_memory import PersonMemoryService
from src.social.asset_manager import AssetManager
from src.social.x_client import XClient
from src.telegram.client.client import TelegramAccountClient
from src.telegram.client.real_client import RealTelegramClient
from src.telegram.handlers.auth import router as auth_router
from src.telegram.handlers.webhook import router as telegram_router

app = FastAPI(title="Mentrast Growth Intelligence")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_dashboard():
    return FileResponse("static/index.html")

app.include_router(telegram_router)
app.include_router(auth_router)

from fastapi import APIRouter, Depends, HTTPException, Header
import os

def verify_admin(x_admin_password: str = Header(default="")):
    expected = os.getenv("ADMIN_PASSWORD", "Mrnaijad")
    if x_admin_password != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

api_router = APIRouter(dependencies=[Depends(verify_admin)])

app.include_router(api_router)

settings = Settings()
database_service = DatabaseService()

conversation_service = ConversationService()
opportunity_service = OpportunityService()
evaluation_service = EvaluationService()
feedback_service = FeedbackService()
outreach_service = OutboundCampaignService()
relationship_manager = RelationshipManager()
person_memory_service = PersonMemoryService(database_service)
automation_controller = AutomationController(
    sleep_minutes=settings.automation_sleep_minutes,
    idle_threshold=settings.automation_idle_threshold,
)
telegram_client = TelegramAccountClient(
    api_id=settings.telegram_api_id,
    api_hash=settings.telegram_api_hash,
    phone=settings.telegram_phone,
)
real_telegram_client = RealTelegramClient(
    api_id=settings.telegram_api_id,
    api_hash=settings.telegram_api_hash,
    phone=settings.telegram_phone,
    database_service=database_service
)
x_client = XClient()
asset_manager = AssetManager()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@api_router.get("/opportunities")
def list_opportunities() -> list[dict[str, object]]:
    return [
        {
            "community": "software engineering learning group",
            "context": "someone asking how to become a developer",
            "stated_goal": "become a software engineer",
            "evidence": "they are learning from YouTube and feel lost",
            "potential_problem": "unclear learning path",
            "mentrast_relevance": "high",
            "confidence": 0.74,
            "recommended_action": "Ask one discovery question",
        }
    ]


@api_router.post("/conversations/{conversation_id}/analyze")
def analyze_conversation(conversation_id: str, message: str) -> dict[str, object]:
    analysis = conversation_service.analyze_message(message)
    database_service.create_conversation(conversation_id=conversation_id, state={
        "goal": analysis.goal,
        "current_learning_method": analysis.current_learning_method,
        "stated_problem": analysis.stated_problem,
        "mentrast_fit": analysis.mentrast_fit,
        "conversation_stage": analysis.conversation_stage,
    })
    return {
        "conversation_id": conversation_id,
        "analysis": {
            "goal": analysis.goal,
            "currentLearningMethod": analysis.current_learning_method,
            "statedProblem": analysis.stated_problem,
            "mentrastFit": analysis.mentrast_fit,
            "conversationStage": analysis.conversation_stage,
            "recommendedAction": analysis.recommended_action,
            "confidence": analysis.confidence,
        },
    }


@api_router.post("/conversations/{conversation_id}/draft")
def draft_response(conversation_id: str, message: str, stage: str) -> dict[str, object]:
    draft = conversation_service.draft_response(message, stage=stage)
    return {
        "conversation_id": conversation_id,
        "draft": draft,
    }


@api_router.post("/conversations/{conversation_id}/outcome")
def record_outcome(conversation_id: str, message: str, stage: str) -> dict[str, object]:
    evaluation = evaluation_service.evaluate(message, stage)
    return {
        "conversation_id": conversation_id,
        "evaluation": {
            "understood_correctly": evaluation.understood_correctly,
            "pitch_too_early": evaluation.pitch_too_early,
            "mentrast_relevant": evaluation.mentrast_relevant,
            "reason": evaluation.reason,
        },
    }


@api_router.post("/conversations/{conversation_id}/feedback")
def record_feedback(conversation_id: str, feedback: str) -> dict[str, object]:
    result = feedback_service.evaluate(feedback)
    person_memory_service.remember(conversation_id, {"feedback": feedback, "feedback_result": result.summary})
    return {
        "conversation_id": conversation_id,
        "feedback_received": result.feedback_received,
        "summary": result.summary,
        "next_action": result.next_action,
    }


@api_router.get("/people/{conversation_id}/memory")
def get_person_memory(conversation_id: str) -> dict[str, object]:
    return {"conversation_id": conversation_id, "memory": person_memory_service.get_memory(conversation_id)}


@api_router.get("/telegram/status")
def telegram_status() -> dict[str, object]:
    status = telegram_client.get_status()
    status["real_client"] = real_telegram_client.get_status()
    return status


@api_router.post("/telegram/connect")
async def telegram_connect() -> dict[str, object]:
    result = await real_telegram_client.connect()
    if result.get("status") in {"connected", "ready", "sent"}:
        automation_controller.mark_channel_activity("telegram", activity="connect")
        start_result = outreach_service.start_daily_cycle(audience="global learners")
        result["automation"] = start_result
    return result


@api_router.post("/automation/start")
def start_automation(audience: str = "global learners") -> dict[str, object]:
    automation_controller.mark_channel_activity("telegram", activity="start")
    return outreach_service.start_daily_cycle(audience=audience)


@api_router.get("/automation/status")
def automation_status() -> dict[str, object]:
    return automation_controller.get_status()


@api_router.post("/automation/tick")
def automation_tick() -> dict[str, object]:
    return automation_controller.tick()


@api_router.post("/telegram/messages/send")
async def send_telegram_message(chat_id: str, message: str, user_id: str | None = None) -> dict[str, object]:
    guard = outreach_service.dispatch_activity("reply")
    if guard.get("status") != "queued":
        return {"status": "blocked", "reason": guard.get("reason", "reply_cap_reached")}
    if user_id and not relationship_manager.should_engage(user_id):
        return {"status": "blocked", "reason": "cooldown_or_blocked"}
    automation_controller.mark_channel_activity("telegram", activity="message")
    if user_id:
        relationship_manager.record_interaction(user_id, channel="telegram", outcome="active", message=message)
    return await real_telegram_client.send_message(chat_id=chat_id, message=message)


@api_router.get("/telegram/chats/{chat_id}/history")
async def get_chat_history(chat_id: str, limit: int = 20) -> dict[str, object]:
    return await real_telegram_client.get_chat_history(chat_id=chat_id, limit=limit)


@api_router.get("/telegram/groups")
async def get_joined_groups(limit: int = 50) -> dict[str, object]:
    """Get a list of currently joined groups."""
    return await real_telegram_client.get_joined_groups(limit=limit)


@api_router.get("/telegram/groups/search")
async def search_and_join_groups(query: str = "tech startup programming developer software", limit: int = 5) -> dict[str, object]:
    """Search for public groups/channels related to tech and automatically join them."""
    return await real_telegram_client.search_and_join_groups(query=query, limit=limit)


@api_router.get("/telegram/groups/{chat_id}/active-users")
async def get_active_users(chat_id: str, limit: int = 100) -> dict[str, object]:
    """Extract users who have sent messages recently in a group."""
    return await real_telegram_client.extract_active_users(chat_id=chat_id, limit=limit)


@api_router.get("/social/x/status")
def x_status() -> dict[str, object]:
    return x_client.get_status()


@api_router.get("/social/x/profile")
def x_profile(topic: str = "learning a new skill") -> dict[str, object]:
    return x_client.get_profile_snapshot(topic=topic)


@api_router.post("/social/x/post")
async def post_to_x(text: str, user_id: str | None = None) -> dict[str, object]:
    guard = outreach_service.dispatch_activity("direct")
    if guard.get("status") != "queued":
        return {"status": "blocked", "reason": guard.get("reason", "direct_cap_reached")}
    if user_id and not relationship_manager.should_engage(user_id):
        return {"status": "blocked", "reason": "cooldown_or_blocked"}
    automation_controller.mark_channel_activity("x", activity="post")
    if user_id:
        relationship_manager.record_interaction(user_id, channel="x", outcome="active", message=text)
    return await x_client.post_tweet(text=text)


@api_router.post("/social/x/reply")
async def reply_to_x(post_id: str, text: str, user_id: str | None = None) -> dict[str, object]:
    guard = outreach_service.dispatch_activity("reply")
    if guard.get("status") != "queued":
        return {"status": "blocked", "reason": guard.get("reason", "reply_cap_reached")}
    if user_id and not relationship_manager.should_engage(user_id):
        return {"status": "blocked", "reason": "cooldown_or_blocked"}
    automation_controller.mark_channel_activity("x", activity="reply")
    if user_id:
        relationship_manager.record_interaction(user_id, channel="x", outcome="active", message=text)
    return await x_client.reply_to_post(post_id=post_id, text=text)


@api_router.post("/social/assets/download")
def download_assets() -> dict[str, object]:
    return asset_manager.download_mentrast_assets()


@api_router.post("/relationship/reply")
def relationship_reply(user_id: str, message: str) -> dict[str, object]:
    reply = relationship_manager.build_persona_reply(user_id, message)
    return {"user_id": user_id, "reply": reply, "status": "ok"}


@api_router.post("/outreach/run")
async def run_outreach(leads: list[dict[str, object]], dry_run: bool = False) -> dict[str, object]:
    result = outreach_service.run_batch(leads=leads, dry_run=dry_run)
    if dry_run or not result["queued_messages"]:
        return result

    sent_messages = []
    failed_messages = []

    for item in result["queued_messages"]:
        chat_id = item.get("chat_id") or item["lead"].get("chat_id")
        if not chat_id:
            failed_messages.append({"item": item, "reason": "missing_chat_id"})
            continue

        send_result = await real_telegram_client.send_message(chat_id=chat_id, message=item["message"])
        if send_result.get("status") == "sent":
            sent_messages.append(send_result)
        else:
            failed_messages.append({"item": item, "result": send_result})

    result["sent_messages"] = sent_messages
    result["failed_messages"] = failed_messages
    return result
