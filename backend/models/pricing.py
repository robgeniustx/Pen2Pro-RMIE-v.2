from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List

class CheckoutRequest(BaseModel):
    tier: str
    email: EmailStr
    user_id: str
    origin_url: Optional[str] = None

class CheckoutResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    checkout_url: Optional[str] = None
    error: Optional[str] = None

class TierInfo(BaseModel):
    name: str
    mode: str
    features: List[str]
    price_display: str
    stripe_price_env: Optional[str] = None
    one_time: bool = False
