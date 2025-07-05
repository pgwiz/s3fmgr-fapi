from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from .file import File
from .folder import Folder

class BrowseResponse(BaseModel):
    """
    Represents the content of a folder for browsing.
    """
    id: UUID
    name: str
    path: str
    owner_id: UUID
    parent_folder_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    files: List[File] = []
    subfolders: List[Folder] = []

    class Config:
        from_attributes = True
