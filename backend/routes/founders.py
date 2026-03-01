from fastapi import APIRouter

router = APIRouter(prefix="/founders", tags=["founders"])

@router.get("/")
def founders():
    return {"ok": True}
