import stripe
from typing import Dict, Any
from core.config import STRIPE_SECRET_KEY
from db.mongo import get_db

stripe.api_key = STRIPE_SECRET_KEY

PLATFORM_TAKE_RATE = 0.20  # 20%

async def release_partner_payout(order_id: str, milestone_id: str) -> Dict[str, Any]:
    """
    Milestone-based payout model.
    Assumes funds are on platform balance (Stripe) and partner is a Connect account.
    Practical note:
    - In production you should use destination charges / separate charges & transfers OR store balance flow.
    - This scaffold records payout intent and triggers a transfer when possible.
    """
    db = get_db()
    order = await db.marketplace_orders.find_one({"id": order_id})
    if not order:
        return {"success": False, "error": "Order not found"}

    partner_account_id = order.get("partner_stripe_account_id")
    if not partner_account_id:
        return {"success": False, "error": "Partner stripe account not set"}

    amount_cents = int(order.get("amount_cents", 0))
    if amount_cents <= 0:
        return {"success": False, "error": "Invalid order amount"}

    partner_share = int(round(amount_cents * (1.0 - PLATFORM_TAKE_RATE)))

    transfer = stripe.Transfer.create(
        amount=partner_share,
        currency=order.get("currency", "usd"),
        destination=partner_account_id,
        metadata={"order_id": order_id, "milestone_id": milestone_id},
    )

    await db.payouts.insert_one({
        "order_id": order_id,
        "milestone_id": milestone_id,
        "transfer_id": transfer.id,
        "amount_cents": partner_share,
        "currency": order.get("currency", "usd"),
        "status": "sent",
        "created_at": __import__("datetime").datetime.utcnow().isoformat(),
    })

    return {"success": True, "transfer_id": transfer.id, "amount_cents": partner_share}
