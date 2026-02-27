import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from db.mongo import get_db
from services.task_service import founder_tasks_for_tier, now_iso
from services.pricing_service import PRICING

UPGRADE_CREDIT_DAYS = 365

def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def _tier_price_cents(tier: str) -> int:
    info = PRICING[tier]
    if info.get("stripe_price_id"):
        # actual collected amount is from Stripe session; use recorded payment amount for credit
        return int(info.get("amount_cents_fallback", 0))
    return int(info.get("amount_cents_fallback", 0))

async def create_founder_records_after_payment(user_id: str, email: str, tier: str, amount_paid_cents: int, stripe_session_id: str):
    db = get_db()
    now = datetime.now(timezone.utc)

    # number of businesses
    biz_count = 1 if tier == "launch_authority" else 2

    founder_id = _new_id("founder")
    founder = {
        "id": founder_id,
        "user_id": user_id,
        "email": email,
        "tier": tier,
        "tier_name": PRICING[tier]["name"],
        "amount_paid_cents": amount_paid_cents,
        "stripe_session_id": stripe_session_id,
        "purchase_date": now.isoformat(),
        "upgrade_credit_expires_at": (now + timedelta(days=UPGRADE_CREDIT_DAYS)).isoformat(),
        "workflow_state": "pending_onboarding",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    await db.founders.insert_one(founder)

    business_ids: List[str] = []
    for i in range(biz_count):
        bid = _new_id("biz")
        business_ids.append(bid)
        await db.businesses.insert_one({
            "id": bid,
            "founder_id": founder_id,
            "business_index": i + 1,
            "business_name": "",
            "status": "draft",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        })

    # Auto-create tasks
    raw_tasks = founder_tasks_for_tier(tier, business_ids)
    tasks = []
    for t in raw_tasks:
        t["founder_id"] = founder_id
        # partner assignment happens later (routing step) but tasks can be created now
        tasks.append(t)

    if tasks:
        await db.tasks.insert_many(tasks)

    return {"founder_id": founder_id, "business_ids": business_ids, "task_count": len(tasks)}

async def compute_upgrade_due(founder: Dict[str, Any], target_tier: str) -> Dict[str, Any]:
    """
    One-year credit policy:
    - within 365 days: credit = amount_paid_cents
    - after: credit = 0
    """
    db = get_db()
    now = datetime.now(timezone.utc)

    paid = int(founder.get("amount_paid_cents", 0))
    expires_at = founder.get("upgrade_credit_expires_at")
    credit = 0

    if expires_at:
        exp = datetime.fromisoformat(expires_at)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now <= exp:
            credit = paid

    target_price = int(PRICING[target_tier].get("amount_cents_fallback", 0))
    due = max(0, target_price - credit)

    return {"credit_cents": credit, "target_price_cents": target_price, "due_cents": due}
