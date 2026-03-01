from typing import Dict, Any
from core.config import (
    STRIPE_PRICE_PRO_MONTHLY,
    STRIPE_PRICE_ELITE_MONTHLY,
    STRIPE_PRICE_LAUNCH_AUTHORITY,
    STRIPE_PRICE_GROWTH_OPERATOR,
    STRIPE_PRICE_VENTURE_ARCHITECT,
)

PRICING: Dict[str, Dict[str, Any]] = {
    "free": {
        "name": "Free Forever",
        "mode": "none",
        "price_display": "$0",
        "features": ["3 RMIE plans/month", "Basic scoring", "Limited dashboard"],
    },
    "pro": {
        "name": "Pro",
        "mode": "subscription",
        "price_display": "$49/mo",
        "stripe_price_id": STRIPE_PRICE_PRO_MONTHLY,
        "features": ["Unlimited RMIE plans", "Deep Research GPT", "Marketplace access (standard)"],
    },
    "elite": {
        "name": "Elite",
        "mode": "subscription",
        "price_display": "$149/mo",
        "stripe_price_id": STRIPE_PRICE_ELITE_MONTHLY,
        "features": ["Execution Architect GPT", "Affiliate Monetization GPT", "Preferred marketplace pricing"],
    },
    "launch_authority": {
        "name": "Launch Authority",
        "mode": "payment",
        "price_display": "$499.99 one-time",
        "stripe_price_id": STRIPE_PRICE_LAUNCH_AUTHORITY,
        "amount_cents_fallback": 49999,
        "features": ["1 Business", "LLC/EIN routed", "Branding", "Website", "Credit roadmap", "Affiliate starter"],
    },
    "growth_operator": {
        "name": "Growth Operator",
        "mode": "payment",
        "price_display": "$999.99 one-time",
        "stripe_price_id": STRIPE_PRICE_GROWTH_OPERATOR,
        "amount_cents_fallback": 99999,
        "features": ["2 Businesses", "CRM setup", "Banking advisory", "Advanced affiliate stack", "Capital roadmap"],
    },
    "venture_architect": {
        "name": "Venture Architect",
        "mode": "payment",
        "price_display": "$1999.99 one-time",
        "stripe_price_id": STRIPE_PRICE_VENTURE_ARCHITECT,
        "amount_cents_fallback": 199999,
        "features": ["Trademark routed", "White-glove onboarding", "Investor-ready docs", "Venture Scale GPT"],
    },
}


def get_pricing_data() -> Dict[str, Dict[str, Any]]:
    return PRICING
