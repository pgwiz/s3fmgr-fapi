from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class BulkDeleteRequest(BaseModel):
    """
    Schema for a bulk delete request.
    """
    file_ids: List[UUID] = []
    folder_ids: List[UUID] = []

class BulkMoveRequest(BaseModel):
    """
    Schema for a bulk move request.
    """
    file_ids: List[UUID] = []
    folder_ids: List[UUID] = []
    target_parent_folder_id: Optional[UUID] = None

class BulkCopyRequest(BaseModel):
    """
    Schema for a bulk copy request.
    """
    file_ids: List[UUID] = []
    folder_ids: List[UUID] = []
    target_parent_folder_id: Optional[UUID] = None

class BulkOperationResponse(BaseModel):
    """
    Generic response for a bulk operation.
    """
    message: str
    deleted_files: int = 0
    deleted_folders: int = 0
    moved_files: int = 0
    moved_folders: int = 0
    copied_files: int = 0
    copied_folders: int = 0
