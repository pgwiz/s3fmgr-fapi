
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.crud import crud_file
from app.services.storage_service import get_storage_service, BaseStorageService

router = APIRouter()

@router.get("/{file_id}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
def get_public_file(
    *,
    db: Session = Depends(get_db),
    file_id: uuid.UUID,
    storage_service: BaseStorageService = Depends(get_storage_service)
):
    """
    Redirects to the permanent public URL of a file if it's public.
    This endpoint requires no authentication.
    """
    db_file = crud_file.get_file_by_id(db, file_id=file_id)

    if not db_file or not db_file.is_public:
        raise HTTPException(status_code=404, detail="Public file not found.")

    public_url = storage_service.get_public_url(file_path=db_file.file_path)
    if not public_url:
        raise HTTPException(status_code=404, detail="Public URL could not be generated.")

    return RedirectResponse(url=public_url)