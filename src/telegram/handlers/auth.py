from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/telegram", tags=["telegram"])

class LoginRequest(BaseModel):
    code: str

@router.post("/auth/send-code")
async def send_code() -> dict[str, object]:
    """Request a login code to be sent to the Telegram app/phone."""
    from src.main import real_telegram_client
    return await real_telegram_client.send_code_request()

@router.post("/auth/login")
async def login(request: LoginRequest) -> dict[str, object]:
    """Submit the login code to complete authentication."""
    from src.main import real_telegram_client
    return await real_telegram_client.sign_in(request.code)
