import os

def env(name: str, default: str | None = None) -> str:
    val = os.environ.get(name, default)
    if val is None:
        raise ValueError(f"{name} not set")
    return val

def env_optional(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)

MONGO_URL = env("MONGO_URL")
DB_NAME = env("DB_NAME")
FRONTEND_URL = env("FRONTEND_URL").rstrip("/")

STRIPE_API_KEY = env("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET")

STRIPE_PRICE_PRO_MONTHLY = env("STRIPE_PRICE_PRO_MONTHLY")
STRIPE_PRICE_ELITE_MONTHLY = env("STRIPE_PRICE_ELITE_MONTHLY")

STRIPE_PRICE_LAUNCH_AUTHORITY = env_optional("STRIPE_PRICE_LAUNCH_AUTHORITY")
STRIPE_PRICE_GROWTH_OPERATOR = env_optional("STRIPE_PRICE_GROWTH_OPERATOR")
STRIPE_PRICE_VENTURE_ARCHITECT = env_optional("STRIPE_PRICE_VENTURE_ARCHITECT")

STRIPE_CONNECT_RETURN_URL = env_optional(
    "STRIPE_CONNECT_RETURN_URL",
    f"{FRONTEND_URL}/partners/return"
)

STRIPE_CONNECT_REFRESH_URL = env_optional(
    "STRIPE_CONNECT_REFRESH_URL",
    f"{FRONTEND_URL}/partners/refresh"
)
