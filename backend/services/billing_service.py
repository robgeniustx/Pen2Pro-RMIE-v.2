import uuid
from typing import Dict, Any, Optional
import stripe

from core.config import (
    STRIPE_SECRET_KEY,
    FRONTEND_URL,
    env_optional,
)
from services.pricing_service import PRICING
from db.mongo import get_db
from services.founder_service import compute_upgrade_due

stripe.api_key = STRIPE_SECRET_KEY

SUCCESS_PATH = env_optional("STRIPE_CHECKOUT_SUCCESS_PATH", "/billing/success")
CANCEL_PATH = env_optional("STRIPE_CHECKOUT_CANCEL_PATH", "/billing/cancel")


def _success_url(origin_url: Optional[str] = None) -> str:
    base = (origin_url or FRONTEND_URL).rstrip("/")
    return f"{base}{SUCCESS_PATH}?session_id={{CHECKOUT_SESSION_ID}}"


def _cancel_url(origin_url: Optional[str] = None) -> str:
    base = (origin_url or FRONTEND_URL).rstrip("/")
    return f"{base}{CANCEL_PATH}"


def _idempotency_key(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


async def create_checkout_for_tier(
    *,
    tier: str,
    user_id: str,
    email: str,
    origin_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates Stripe Checkout Session for:
      - subscription tiers (pro, elite) using configured price IDs
      - founder one-time tiers using configured price IDs
    """
    if tier not in PRICING:
        return {"success": False, "error": f"Unknown tier: {tier}"}

    tinfo = PRICING[tier]
    mode = tinfo["mode"]

    price_id = tinfo.get("stripe_price_id")
    if mode in ("subscription", "payment") and not price_id:
        return {"success": False, "error": f"Stripe price_id not configured for tier: {tier}"}

    metadata = {
        "tier": tier,
        "user_id": user_id,
        "email": email,
        "product": "pen2pro_v2",
    }

    # record intent in DB (optional but helpful)
    db = get_db()
    intent_id = f"intent_{uuid.uuid4().hex[:12]}"
    await db.checkout_intents.insert_one({
        "id": intent_id,
        "tier": tier,
        "mode": mode,
        "user_id": user_id,
        "email": email,
        "origin_url": origin_url or FRONTEND_URL,
        "status": "created",
        "created_at": __import__("datetime").datetime.utcnow().isoformat(),
    })
    metadata["intent_id"] = intent_id

    try:
        session = stripe.checkout.Session.create(
            mode=("subscription" if mode == "subscription" else "payment"),
            customer_email=email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=_success_url(origin_url),
            cancel_url=_cancel_url(origin_url),
            metadata=metadata,
            allow_promotion_codes=True if mode == "subscription" else False,
        , idempotency_key=_idempotency_key("co"))
    except TypeError:
        # Some stripe versions don't accept idempotency_key kwarg on create;
        # fallback without it.
        session = stripe.checkout.Session.create(
            mode=("subscription" if mode == "subscription" else "payment"),
            customer_email=email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=_success_url(origin_url),
            cancel_url=_cancel_url(origin_url),
            metadata=metadata,
            allow_promotion_codes=True if mode == "subscription" else False,
        )

    await db.checkout_intents.update_one(
        {"id": intent_id},
        {"$set": {"status": "session_created", "stripe_session_id": session.id}}
    )

    return {"success": True, "session_id": session.id, "checkout_url": session.url}


async def create_founder_upgrade_checkout(
    *,
    user_id: str,
    target_tier: str,
    origin_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Founder upgrade checkout with 1-year credit applied.
    Charges ONLY the due amount (difference) using price_data (no extra Stripe Prices needed).
    """
    if target_tier not in ("growth_operator", "venture_architect"):
        return {"success": False, "error": "target_tier must be growth_operator or venture_architect"}

    db = get_db()
    founder = await db.founders.find_one({"user_id": user_id}, {"_id": 0})
    if not founder:
        return {"success": False, "error": "Founder record not found for user"}

    quote = await compute_upgrade_due(founder, target_tier)
    due_cents = int(quote["due_cents"])
    if due_cents <= 0:
        return {"success": False, "error": "No payment due (already covered by credit or same tier)"}

    email = founder.get("email", "")

    metadata = {
        "tier": target_tier,
        "user_id": user_id,
        "email": email,
        "product": "pen2pro_v2",
        "upgrade_from": founder.get("tier"),
        "upgrade_credit_cents": str(int(quote["credit_cents"])),
        "upgrade_due_cents": str(due_cents),
        "upgrade": "true",
    }

    # record upgrade intent
    intent_id = f"upg_{uuid.uuid4().hex[:12]}"
    await db.checkout_intents.insert_one({
        "id": intent_id,
        "type": "founder_upgrade",
        "from_tier": founder.get("tier"),
        "to_tier": target_tier,
        "user_id": user_id,
        "email": email,
        "credit_cents": int(quote["credit_cents"]),
        "due_cents": due_cents,
        "status": "created",
        "created_at": __import__("datetime").datetime.utcnow().isoformat(),
    })
    metadata["intent_id"] = intent_id

    # Use price_data so you can charge the difference without creating extra Prices in Stripe
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            customer_email=email,
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"PEN2PRO Founder Upgrade → {PRICING[target_tier]['name']}",
                    },
                    "unit_amount": due_cents,
                },
                "quantity": 1
            }],
            success_url=_success_url(origin_url),
            cancel_url=_cancel_url(origin_url),
            metadata=metadata,
        , idempotency_key=_idempotency_key("upg"))
    except TypeError:
        session = stripe.checkout.Session.create(
            mode="payment",
            customer_email=email,
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"PEN2PRO Founder Upgrade → {PRICING[target_tier]['name']}",
                    },
                    "unit_amount": due_cents,
                },
                "quantity": 1
            }],
            success_url=_success_url(origin_url),
            cancel_url=_cancel_url(origin_url),
            metadata=metadata,
        )

    await db.checkout_intents.update_one(
        {"id": intent_id},
        {"$set": {"status": "session_created", "stripe_session_id": session.id}}
    )

    return {
        "success": True,
        "session_id": session.id,
        "checkout_url": session.url,
        "quote": quote,
    }
