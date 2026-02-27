import uuid
import stripe
from typing import Dict, Any
from core.config import STRIPE_CONNECT_RETURN_URL, STRIPE_CONNECT_REFRESH_URL
from db.mongo import get_db
from core.config import STRIPE_SECRET_KEY

stripe.api_key = STRIPE_SECRET_KEY

def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

async def create_partner(email: str, business_name: str) -> Dict[str, Any]:
    db = get_db()
    partner_id = _new_id("partner")
    await db.partners.insert_one({
        "id": partner_id,
        "email": email,
        "business_name": business_name,
        "active": True,
        "created_at": __import__("datetime").datetime.utcnow().isoformat(),
    })
    return {"partner_id": partner_id}

async def onboard_partner_express(partner_id: str, email: str) -> Dict[str, Any]:
    """
    Creates/attaches a Stripe Connect Express account and returns onboarding link.
    """
    db = get_db()

    existing = await db.partner_accounts.find_one({"partner_id": partner_id})
    if existing and existing.get("stripe_account_id"):
        acct_id = existing["stripe_account_id"]
    else:
        acct = stripe.Account.create(
            type="express",
            email=email,
            capabilities={"transfers": {"requested": True}},
        )
        acct_id = acct.id
        await db.partner_accounts.update_one(
            {"partner_id": partner_id},
            {"$set": {"partner_id": partner_id, "stripe_account_id": acct_id}},
            upsert=True
        )

    link = stripe.AccountLink.create(
        account=acct_id,
        refresh_url=STRIPE_CONNECT_REFRESH_URL,
        return_url=STRIPE_CONNECT_RETURN_URL,
        type="account_onboarding"
    )

    return {"success": True, "account_id": acct_id, "onboarding_url": link.url}
