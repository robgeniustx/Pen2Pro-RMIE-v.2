from fastapi import APIRouter
from typing import Optional
import os

router = APIRouter()

def get_env(name: str) -> Optional[str]:
    return os.getenv(name)

@router.get("/api/pricing")
def get_pricing():
    """
    Returns Stripe price IDs configured in environment variables.
    Does NOT crash if missing.
    """

    return {
        "pro_monthly": get_env("STRIPE_PRICE_PRO_MONTHLY"),
        "elite_monthly": get_env("STRIPE_PRICE_ELITE_MONTHLY"),
        "launch_authority": get_env("STRIPE_PRICE_LAUNCH_AUTHORITY"),
        "growth_operator": get_env("STRIPE_PRICE_GROWTH_OPERATOR"),
        "venture_architect": get_env("STRIPE_PRICE_VENTURE_ARCHITECT"),
    }


@router.get("/api/pricing/health")
def pricing_health():
    return {"status": "pricing router active"}
