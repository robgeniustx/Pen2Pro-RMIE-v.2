from fastapi import APIRouter

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

@router.get("/")
def marketplace():
    return {"ok": True}
