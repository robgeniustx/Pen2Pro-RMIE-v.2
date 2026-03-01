from fastapi import APIRouter

router = APIRouter(prefix="/partners", tags=["partners"])

@router.get("/")
def partners():
    return {"ok": True}
