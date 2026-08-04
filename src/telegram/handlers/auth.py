from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
import os

def verify_admin(x_admin_password: str = Header(default="")):
    expected = os.getenv("ADMIN_PASSWORD", "Mrnaijad")
    if x_admin_password != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

router = APIRouter(prefix="/telegram", tags=["telegram"], dependencies=[Depends(verify_admin)])

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
