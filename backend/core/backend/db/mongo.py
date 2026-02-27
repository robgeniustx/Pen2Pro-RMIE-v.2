from motor.motor_asyncio import AsyncIOMotorClient
from core.config import MONGO_URL, DB_NAME

_client = None
_db = None

def get_client():
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URL)
    return _client

def get_db():
    global _db
    if _db is None:
        _db = get_client()[DB_NAME]
    return _db
