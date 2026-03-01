import logging
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from db.mongo import get_client

# Routers
from routes.health import router as health_router
from routes.pricing import router as pricing_router
from routes.founders import router as founders_router
from routes.partners import router as partners_router
from routes.marketplace import router as marketplace_router
from routes.billing import router as billing_router
from routes.stripe_webhooks import router as stripe_webhook_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PEN2PRO_V2")

# Create app ONCE
app = FastAPI(title="PEN2PRO V2", version="2.0.0")

# CORS (tighten allow_origins later to your real frontend domain)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup: init DB client (idempotent if your get_client() is)
@app.on_event("startup")
async def startup():
    _ = get_client()
    logger.info("Mongo client initialized")

# Basic root
@app.get("/")
async def root():
    return {"status": "ok", "service": "PEN2PRO V2"}

# Register routers
app.include_router(health_router)
app.include_router(pricing_router)
app.include_router(founders_router)
app.include_router(partners_router)
app.include_router(marketplace_router)
app.include_router(billing_router)
app.include_router(stripe_webhook_router)
