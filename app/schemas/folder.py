from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from .file import File # Import the File schema

# --- Base Schema ---
class FolderBase(BaseModel):
    name: str
    parent_folder_id: Optional[UUID] = None

# --- Schema for Creation ---
class FolderCreate(FolderBase):
    pass

# --- Schema for Updating (e.g., rename) ---
class FolderUpdate(BaseModel):
    name: Optional[str] = None

# --- NEW Schema for Moving ---
class FolderMove(BaseModel):
    parent_folder_id: Optional[UUID] = None

# --- Schema for Reading/Returning from API ---
class Folder(FolderBase):
    id: UUID
    owner_id: UUID
    path: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Schema for Folder with Content ---
class FolderWithContent(Folder):
    subfolders: List[Folder] = []
    files: List[File] = []

    class Config:
        from_attributes = True
