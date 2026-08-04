from fastapi import APIRouter

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/code")
async def request_code() -> dict[str, str]:
    return {"status": "ready", "message": "Use the real Telegram client flow to request a code from the account."}
