from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

# --- Token Schemas ---
class Token(BaseModel):
    """
    Pydantic model for the access token response.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Pydantic model for the data contained within a token.
    """
    email: Optional[str] = None

# --- Base Schema ---
class UserBase(BaseModel):
    email: EmailStr
    role: str = "user"

# --- Schema for Creation ---
class UserCreate(UserBase):
    password: str

# --- Schema for Reading/Returning from API ---
class User(UserBase):
    id: UUID
    storage_quota: int
    used_storage: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True