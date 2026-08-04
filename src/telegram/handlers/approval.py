from fastapi import APIRouter

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("/")
async def list_approvals() -> dict[str, object]:
    return {"status": "deprecated", "note": "Approval endpoints are deprecated; use direct outbound execution."}
