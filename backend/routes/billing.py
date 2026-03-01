from fastapi import APIRouter, Body
from services.billing_service import create_checkout_session

router = APIRouter(prefix="/billing", tags=["billing"])

@router.post("/checkout")
async def checkout(payload: dict = Body(...)):
    # Expected payload keys (adjust to your frontend):
    # plan, user_id, email, origin_url(optional), intent_id(optional), customer_id(optional), ref_id(optional)
    return await create_checkout_session(
        plan=payload["plan"],
        user_id=payload["user_id"],
        email=payload["email"],
        origin_url=payload.get("origin_url"),
        intent_id=payload.get("intent_id"),
        customer_id=payload.get("customer_id"),
        ref_id=payload.get("ref_id"),
    )
