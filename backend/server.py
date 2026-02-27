import logging
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from db.mongo import get_client

from routes.health import router as health_router
from routes.pricing import router as pricing_router
from routes.founders import router as founders_router
from routes.partners import router as partners_router
from routes.marketplace import router as marketplace_router
from routes.stripe_webhooks import router as stripe_router
from routes.billing import router as billing_router  # <-- NEW

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PEN2PRO_V2")

app = FastAPI(title="PEN2PRO v2", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],  # tighten to your frontend domain later
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    _ = get_client()
    logger.info("Mongo client initialized")

@app.get("/api")
async def root():
    return {"message": "PEN2PRO v2 API running"}

# Routers
app.include_router(health_router)
app.include_router(pricing_router)
app.include_router(founders_router)
app.include_router(partners_router)
app.include_router(marketplace_router)
app.include_router(stripe_router)
app.include_router(billing_router)  # <-- NEW
