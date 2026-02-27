from fastapi import APIRouter, Request, Header, HTTPException
import stripe
import os

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_API_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")


@router.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle event types
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print("Checkout completed:", session["id"])

    elif event["type"] == "invoice.paid":
        print("Invoice paid")

    elif event["type"] == "customer.subscription.deleted":
        print("Subscription canceled")

    return {"status": "success"}
