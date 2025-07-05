from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID

from app.schemas.folder import Folder, FolderCreate, FolderWithContent, FolderUpdate, FolderMove
from app.models.user import User as UserModel
from app.core.database import get_db
from app.api.v1 import deps
from app.crud import crud_folder

router = APIRouter()

@router.post("/", response_model=Folder, status_code=status.HTTP_201_CREATED)
def create_folder(
    *,
    db: Session = Depends(get_db),
    folder_in: FolderCreate,
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Create a new folder.
    """
    folder = crud_folder.create_folder(db=db, folder_in=folder_in, owner=current_user)
    if not folder:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent folder not found or you don't have permission to access it.",
        )
    return folder


@router.get("/{folder_id}", response_model=FolderWithContent)
def read_folder(
    *,
    db: Session = Depends(get_db),
    folder_id: UUID,
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Get a specific folder by ID, including its contents.
    
    This endpoint is protected and returns the folder's details,
    a list of its subfolders, and a list of its files.
    """
    folder = crud_folder.get_folder(db=db, folder_id=folder_id, owner_id=current_user.id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found or you don't have permission to access it.",
        )
    return folder

@router.put("/{folder_id}/rename", response_model=Folder)
def rename_folder(
    *,
    db: Session = Depends(get_db),
    folder_id: UUID,
    folder_in: FolderUpdate,
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Rename a folder.
    """
    db_folder = crud_folder.get_folder(db=db, folder_id=folder_id, owner_id=current_user.id)
    if not db_folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found or access denied.",
        )
    
    # TODO: Add validation to prevent renaming to a name that already exists
    # in the same parent directory.
    
    updated_folder = crud_folder.rename_folder(db=db, db_folder=db_folder, folder_in=folder_in)
    return updated_folder

@router.put("/{folder_id}/move", response_model=Folder)
def move_folder(
    *,
    db: Session = Depends(get_db),
    folder_id: UUID,
    folder_in: FolderMove,
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Move a folder to a new parent folder.
    """
    db_folder = crud_folder.get_folder(db=db, folder_id=folder_id, owner_id=current_user.id)
    if not db_folder:
        raise HTTPException(status_code=404, detail="Folder to move not found or access denied.")

    new_parent_path = "/"
    target_parent_id = folder_in.parent_folder_id

    # Validate the move
    if target_parent_id:
        if target_parent_id == db_folder.id:
            raise HTTPException(status_code=400, detail="Cannot move a folder into itself.")

        target_parent_folder = crud_folder.get_folder(db, folder_id=target_parent_id, owner_id=current_user.id)
        if not target_parent_folder:
            raise HTTPException(status_code=404, detail="Target folder not found or access denied.")
        
        if target_parent_folder.path.startswith(db_folder.path + '/'):
            raise HTTPException(status_code=400, detail="Cannot move a folder into one of its own subfolders.")
        
        new_parent_path = target_parent_folder.path

    updated_folder = crud_folder.move_folder(
        db=db, 
        db_folder=db_folder, 
        new_parent_path=new_parent_path, 
        new_parent_id=target_parent_id
    )
    return updated_folder

@router.delete("/{folder_id}", status_code=status.HTTP_200_OK)
def delete_folder(
    *,
    db: Session = Depends(get_db),
    folder_id: UUID,
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Delete a folder and all of its contents.
    This action is irreversible.
    """
    success = crud_folder.delete_folder(db=db, folder_id=folder_id, owner_id=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found or you don't have permission to access it.",
        )
    return JSONResponse(content={"message": "Folder and its contents deleted successfully"})
