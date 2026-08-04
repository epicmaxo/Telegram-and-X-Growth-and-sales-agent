from fastapi import APIRouter

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.get("/setup")
async def telegram_setup() -> dict[str, str]:
    return {
        "mode": "user-account",
        "instruction": "Set TELEGRAM_API_ID, TELEGRAM_API_HASH, and TELEGRAM_PHONE in your environment, then run the connect flow.",
    }
