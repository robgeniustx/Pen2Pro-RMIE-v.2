from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserOut(BaseModel):
    user_id: str
    email: EmailStr
    name: str
    tier: str = "free"
    founder_tier: Optional[str] = None
