from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.bulk import BulkDeleteRequest, BulkMoveRequest, BulkCopyRequest, BulkOperationResponse
from app.models.user import User as UserModel
from app.core.database import get_db
from app.api.v1 import deps
from app.crud import crud_bulk

router = APIRouter()

@router.post("/delete", response_model=BulkOperationResponse)
def bulk_delete_items(
    *,
    db: Session = Depends(get_db),
    bulk_in: BulkDeleteRequest,
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Perform a bulk delete of files and folders.
    """
    if not bulk_in.file_ids and not bulk_in.folder_ids:
        raise HTTPException(status_code=400, detail="No file or folder IDs provided.")
    result = crud_bulk.bulk_delete(db=db, bulk_in=bulk_in, owner_id=current_user.id)
    return {"message": "Bulk delete operation completed.", **result}

@router.post("/move", response_model=BulkOperationResponse)
def bulk_move_items(
    *,
    db: Session = Depends(get_db),
    bulk_in: BulkMoveRequest,
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Perform a bulk move of files and folders.
    """
    if not bulk_in.file_ids and not bulk_in.folder_ids:
        raise HTTPException(status_code=400, detail="No file or folder IDs provided.")
    result = crud_bulk.bulk_move(db=db, bulk_in=bulk_in, owner_id=current_user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Target folder not found or access denied.")
    return {"message": "Bulk move operation completed.", **result}

# --- NEW ENDPOINT ---
@router.post("/copy", response_model=BulkOperationResponse)
def bulk_copy_items(
    *,
    db: Session = Depends(get_db),
    bulk_in: BulkCopyRequest,
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Perform a bulk copy of files and folders.
    """
    if not bulk_in.file_ids and not bulk_in.folder_ids:
        raise HTTPException(status_code=400, detail="No file or folder IDs provided.")

    # TODO: Add validation to prevent copying a folder into itself or a subfolder.

    result = crud_bulk.bulk_copy(db=db, bulk_in=bulk_in, owner=current_user)
    if result is None:
        raise HTTPException(status_code=404, detail="Target folder not found or access denied.")

    return {
        "message": "Bulk copy operation completed.",
        **result
    }
