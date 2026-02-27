from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class PartnerOnboardRequest(BaseModel):
    partner_id: str
    email: str
    business_name: str

class PartnerOnboardResponse(BaseModel):
    success: bool
    account_id: Optional[str] = None
    onboarding_url: Optional[str] = None
    error: Optional[str] = None

class MilestoneApproveRequest(BaseModel):
    order_id: str
    milestone_id: str
    approved_by: str = "admin"
    notes: str = ""
