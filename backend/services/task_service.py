import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

INTERNAL_CATEGORIES = {"branding", "website", "credit_roadmap", "crm_setup", "banking_advisory"}
PARTNER_CATEGORIES = {"llc_ein", "trademark"}

def build_task(founder_id: str, business_id: str | None, category: str, title: str, assigned_type: str, assigned_id: str | None):
    return {
        "id": str(uuid.uuid4()),
        "founder_id": founder_id,
        "business_id": business_id,
        "category": category,
        "title": title,
        "status": "not_started",
        "assigned_type": assigned_type,   # "internal" or "partner"
        "assigned_id": assigned_id,       # partner_id if partner
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

def founder_tasks_for_tier(tier: str, business_ids: List[str]) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []

    def add_per_business(category: str, title: str, assigned_type: str, assigned_id=None):
        for bid in business_ids:
            tasks.append(build_task(founder_id="__F__", business_id=bid, category=category, title=title, assigned_type=assigned_type, assigned_id=assigned_id))

    def add_founder_level(category: str, title: str, assigned_type: str, assigned_id=None):
        tasks.append(build_task(founder_id="__F__", business_id=None, category=category, title=title, assigned_type=assigned_type, assigned_id=assigned_id))

    # Always include
    add_per_business("branding", "Brand Identity Package", "internal")
    add_per_business("website", "Website Build (Template-Based)", "internal")
    add_per_business("credit_roadmap", "Credit Readiness Roadmap", "internal")
    add_per_business("llc_ein", "LLC + EIN Setup (Partner Routed)", "partner")

    if tier in ("growth_operator", "venture_architect"):
        add_founder_level("crm_setup", "CRM Setup", "internal")
        add_founder_level("banking_advisory", "Business Banking Advisory", "internal")

    if tier == "venture_architect":
        add_per_business("trademark", "Trademark Routing (Partner)", "partner")

    return tasks
