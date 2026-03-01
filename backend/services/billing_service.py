from __future__ import annotations

import os
import hashlib
from typing import Any, Dict, Optional

import stripe

from core.config import (
    FRONTEND_URL,
    STRIPE_API_KEY,
    STRIPE_PRICE_PRO_MONTHLY,
    STRIPE_PRICE_ELITE_MONTHLY,
    STRIPE_PRICE_LAUNCH_AUTHORITY,
    STRIPE_PRICE_GROWTH_OPERATOR,
    STRIPE_PRICE_VENTURE_ARCHITECT,
)

# If you store checkout intents in Mongo, keep this import.
# If your project uses a different DB accessor, replace accordingly.
from db.mongo import get_client


stripe.api_key = STRIPE_API_KEY


def _idempotency_key(prefix: str, seed: str | None = None) -> str:
    """
    Deterministic-ish idempotency key to prevent duplicate Stripe objects.
    You can pass a unique seed (e.g., intent_id, user_id, etc.).
    """
    raw = f"{prefix}:{seed or os.urandom(16).hex()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _success_url(origin_url: Optional[str] = None) -> str:
    base = (origin_url or FRONTEND_URL).rstrip("/")
    return f"{base}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"


def _cancel_url(origin_url: Optional[str] = None) -> str:
    base = (origin_url or FRONTEND_URL).rstrip("/")
    return f"{base}/billing/cancel"


def _price_id_for_plan(plan: str) -> str:
    plan = (plan or "").strip().lower()

    if plan == "pro":
        if not STRIPE_PRICE_PRO_MONTHLY:
            raise ValueError("STRIPE_PRICE_PRO_MONTHLY not set")
        return STRIPE_PRICE_PRO_MONTHLY

    if plan == "elite":
        if not STRIPE_PRICE_ELITE_MONTHLY:
            raise ValueError("STRIPE_PRICE_ELITE_MONTHLY not set")
        return STRIPE_PRICE_ELITE_MONTHLY

    if plan == "launch_authority":
        if not STRIPE_PRICE_LAUNCH_AUTHORITY:
            raise ValueError("STRIPE_PRICE_LAUNCH_AUTHORITY not set")
        return STRIPE_PRICE_LAUNCH_AUTHORITY

    if plan == "growth_operator":
        if not STRIPE_PRICE_GROWTH_OPERATOR:
            raise ValueError("STRIPE_PRICE_GROWTH_OPERATOR not set")
        return STRIPE_PRICE_GROWTH_OPERATOR

    if plan == "venture_architect":
        if not STRIPE_PRICE_VENTURE_ARCHITECT:
            raise ValueError("STRIPE_PRICE_VENTURE_ARCHITECT not set")
        return STRIPE_PRICE_VENTURE_ARCHITECT

    raise ValueError(f"Unknown plan: {plan}")


def _mode_for_plan(plan: str) -> str:
    """
    Return Stripe Checkout mode: 'subscription' for monthly plans, 'payment' for one-time.
    """
    plan = (plan or "").strip().lower()
    if plan in {"pro", "elite"}:
        return "subscription"
    if plan in {"launch_authority", "growth_operator", "venture_architect"}:
        return "payment"
    raise ValueError(f"Unknown plan: {plan}")


async def create_checkout_session(
    *,
    plan: str,
    user_id: str,
    email: str,
    origin_url: Optional[str] = None,
    intent_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    ref_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates a Stripe Checkout Session and stores a lightweight record (optional) in Mongo.

    Parameters you likely already have:
      - plan: 'pro'|'elite'|'launch_authority'|'growth_operator'|'venture_architect'
      - user_id/email: who is checking out
      - origin_url: frontend base (optional); defaults to FRONTEND_URL
      - intent_id: your internal checkout intent id (optional)
      - customer_id: existing Stripe customer id (optional)
      - ref_id: client_reference_id (optional)
    """
    price_id = _price_id_for_plan(plan)
    mode = _mode_for_plan(plan)

    success_url = _success_url(origin_url)
    cancel_url = _cancel_url(origin_url)

    # Stripe expects line_items list in a consistent format
    line_items = [{"price": price_id, "quantity": 1}]

    metadata: Dict[str, Any] = {
        "plan": plan,
        "user_id": user_id,
        "email": email,
        "origin_url": (origin_url or FRONTEND_URL),
        "status": "created",
    }
    if intent_id:
        metadata["intent_id"] = intent_id

    # Create Stripe Checkout Session (single, correct call; no duplicate kwargs)
    try:
        session = stripe.checkout.Session.create(
            mode=mode,
            customer_email=email,
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            customer=customer_id,
            client_reference_id=ref_id,
            metadata=metadata,
            idempotency_key=_idempotency_key("co", seed=intent_id or ref_id or user_id),
        )
    except TypeError:
        # Some Stripe versions don't accept idempotency_key kwarg on create; fallback.
        session = stripe.checkout.Session.create(
            mode=mode,
            customer_email=email,
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            customer=customer_id,
            client_reference_id=ref_id,
            metadata=metadata,
        )

    # Optional: store/update a checkout intent record in Mongo if you have that collection.
    # If your DB schema differs, adjust or remove this block safely.
    if intent_id:
        client = get_client()
        db = client.get_default_database()

        await db.checkout_intents.update_one(
            {"id": intent_id},
            {
                "$set": {
                    "status": "session_created",
                    "stripe_session_id": session.id,
                    "stripe_session_url": getattr(session, "url", None),
                    "plan": plan,
                    "mode": mode,
                    "user_id": user_id,
                    "email": email,
                    "origin_url": (origin_url or FRONTEND_URL),
                }
            },
            upsert=True,
        )

    return {
        "id": session.id,
        "url": getattr(session, "url", None),
        "mode": mode,
        "price_id": price_id,
    }
