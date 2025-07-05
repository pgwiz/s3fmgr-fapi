from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.api.v1 import deps
from app.models.user import User as UserModel
from app.models.folder import Folder
from app.models.file import File
from app.schemas.browse import BrowseResponse

router = APIRouter()

@router.get("/", response_model=BrowseResponse)
def browse_content(
    *,
    db: Session = Depends(get_db),
    folder_id: Optional[UUID] = Query(None),
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Browse the contents of a folder or the root directory.
    
    - If `folder_id` is provided, it returns the contents of that folder.
    - If `folder_id` is omitted, it returns the root-level files and folders for the user.
    """
    if folder_id:
        # Get a specific folder's content
        folder = db.query(Folder).filter(Folder.id == folder_id, Folder.owner_id == current_user.id).first()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found or you don't have permission to access it.")
        
        # Manually load files and subfolders for the response model
        folder.files = db.query(File).filter(File.parent_folder_id == folder_id).all()
        folder.subfolders = db.query(Folder).filter(Folder.parent_folder_id == folder_id).all()
        return folder
    else:
        # Get root content (items with no parent folder)
        root_folders = db.query(Folder).filter(Folder.owner_id == current_user.id, Folder.parent_folder_id == None).all()
        root_files = db.query(File).filter(File.owner_id == current_user.id, File.parent_folder_id == None).all()
        
        # Construct a "virtual" root folder to hold the response
        root_node = {
            "id": current_user.id,
            "name": "Root",
            "path": "/",
            "owner_id": current_user.id,
            "parent_folder_id": None,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at,
            "files": root_files,
            "subfolders": root_folders
        }
        return root_node
