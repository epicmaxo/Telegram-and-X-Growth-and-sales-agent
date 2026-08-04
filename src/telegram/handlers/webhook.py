from fastapi import APIRouter, Request

router = APIRouter(prefix="/webhooks", tags=["telegram"])


@router.post("/telegram")
async def telegram_webhook(request: Request) -> dict[str, object]:
    payload = await request.json()
    return {
        "status": "received",
        "update_id": str(payload.get("update_id", "unknown")),
        "mode": "user-account",
        "note": "This endpoint accepts Telegram updates. For V1, the account client is used to read and send messages through the signed-in account.",
    }
