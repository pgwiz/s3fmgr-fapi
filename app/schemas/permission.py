from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum

class PermissionType(str, Enum):
    READ = "read"
    WRITE = "write"

class PermissionCreate(BaseModel):
    user_email: EmailStr
    permission_type: PermissionType
    expires_at: Optional[datetime] = None

class Permission(BaseModel):
    id: UUID
    user_id: UUID
    permission_type: str
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True
