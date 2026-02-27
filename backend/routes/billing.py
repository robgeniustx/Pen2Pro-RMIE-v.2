from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional

from services.billing_service import (
    create_checkout_for_tier,
    create_founder_upgrade_checkout,
)

router = APIRouter(prefix="/api/billing", tags=["billing"])


class TierCheckoutRequest(BaseModel):
    tier: str
    user_id: str
    email: EmailStr
    origin_url: Optional[str] = None


class FounderUpgradeCheckoutRequest(BaseModel):
    user_id: str
    target_tier: str  # growth_operator or venture_architect
    origin_url: Optional[str] = None


@router.post("/checkout")
async def checkout(req: TierCheckoutRequest):
    result = await create_checkout_for_tier(
        tier=req.tier,
        user_id=req.user_id,
        email=req.email,
        origin_url=req.origin_url,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Checkout failed"))
    return result


@router.post("/founder-upgrade-checkout")
async def founder_upgrade_checkout(req: FounderUpgradeCheckoutRequest):
    result = await create_founder_upgrade_checkout(
        user_id=req.user_id,
        target_tier=req.target_tier,
        origin_url=req.origin_url,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Upgrade checkout failed"))
    return result
