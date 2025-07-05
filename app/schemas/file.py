from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

# --- Base Schema ---
class FileBase(BaseModel):
    original_name: str
    mime_type: str
    size: int

# --- Schema for Creation (Internal Use) ---
class FileCreate(FileBase):
    filename: str
    file_path: str
    hash_sha256: str
    owner_id: UUID
    parent_folder_id: Optional[UUID] = None

# --- Schema for Updating (e.g., rename) ---
class FileUpdate(BaseModel):
    original_name: Optional[str] = None

# --- NEW Schema for Moving ---
class FileMove(BaseModel):
    parent_folder_id: Optional[UUID] = None

# --- Schema for Reading/Returning from API ---
class File(FileBase):
    id: UUID
    filename: str
    owner_id: UUID
    parent_folder_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
