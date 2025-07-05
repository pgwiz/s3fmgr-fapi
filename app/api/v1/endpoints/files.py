import hashlib
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, Form, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.schemas.permission import PermissionCreate, Permission
from app.crud import crud_permission
from uuid import UUID
from app.schemas.file import File as FileSchema
from app.models.user import User as UserModel
from app.core.database import get_db
from app.api.v1 import deps
from app.crud import crud_file, crud_folder
from app.schemas.file import FileCreate, FileUpdate, FileMove
from app.services.storage_service import get_storage_service, BaseStorageService
from app.schemas.upload import (
    UploadSessionInitiateRequest,
    UploadSessionInitiateResponse,
    UploadChunkResponse,
)
from app.crud import crud_upload_session
from app.core.config import settings
# File: app/api/v1/endpoints/files.py
router = APIRouter()

@router.post("/upload", response_model=FileSchema, status_code=status.HTTP_201_CREATED)
def upload_file(
    *,
    db: Session = Depends(get_db),
    parent_folder_id: uuid.UUID | None = Form(None),
    file: UploadFile = FastAPIFile(...),
    current_user: UserModel = Depends(deps.get_current_user),
    storage_service: BaseStorageService = Depends(get_storage_service)
):
    if parent_folder_id:
        parent_folder = crud_folder.get_folder(db, folder_id=parent_folder_id, owner_id=current_user.id)
        if not parent_folder:
            raise HTTPException(status_code=404, detail="Parent folder not found or access denied.")

    file_content = file.file.read()
    file_size = len(file_content)
    file.file.seek(0)
    
    if current_user.used_storage + file_size > current_user.storage_quota:
        raise HTTPException(status_code=400, detail="Insufficient storage quota.")

    saved_path, saved_filename = storage_service.save(file=file, user_id=str(current_user.id))
    
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    file_in = FileCreate(
        original_name=file.filename,
        filename=saved_filename,
        file_path=saved_path,
        size=file_size,
        mime_type=file.content_type,
        hash_sha256=file_hash,
        owner_id=current_user.id,
        parent_folder_id=parent_folder_id
    )
    db_file = crud_file.create_file(db=db, file_in=file_in)
    return db_file

@router.get("/{file_id}/download")
def download_file(
    *,
    db: Session = Depends(get_db),
    file_id: uuid.UUID,
    current_user: UserModel = Depends(deps.get_current_user),
    storage_service: BaseStorageService = Depends(get_storage_service)
):
    db_file = crud_file.get_file_by_id(db, file_id=file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found.")
        
    # Simplified permission check needed here
    # if not crud_permission.has_read_permission(db, db_file=db_file, user=current_user):
    #     raise HTTPException(status_code=403, detail="Not enough permissions.")

    download_url = storage_service.get_download_url(file_path=db_file.file_path, filename=db_file.original_name)
    
    if settings.STORAGE_TYPE == 's3':
        return RedirectResponse(url=download_url)
    else:
        return FileResponse(path=download_url, media_type=db_file.mime_type, filename=db_file.original_name)


@router.get("/{file_id}/info", response_model=FileSchema)
def get_file_info(
    *,
    db: Session = Depends(get_db),
    file_id: uuid.UUID,
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Get a specific file's metadata by its ID.
    """
    db_file = crud_file.get_file_by_id(db, file_id=file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found.")
    
    if not crud_permission.has_read_permission(db, db_file=db_file, user=current_user):
        raise HTTPException(status_code=403, detail="Not enough permissions.")
    
    return db_file

@router.delete("/{file_id}")
def delete_file(
    *,
    db: Session = Depends(get_db),
    file_id: uuid.UUID,
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Delete a file (uses storage service via CRUD layer).
    """
    deleted_file = crud_file.delete_file(db=db, file_id=file_id, owner_id=current_user.id)
    if not deleted_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or you don't have permission to access it.",
        )
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "File deleted successfully"})

@router.put("/{file_id}/rename", response_model=FileSchema)
def rename_file(
    *,
    db: Session = Depends(get_db),
    file_id: uuid.UUID,
    file_in: FileUpdate,
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Rename a file.
    """
    db_file = crud_file.get_file(db=db, file_id=file_id, owner_id=current_user.id)
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or access denied.",
        )
    
    updated_file = crud_file.rename_file(db=db, db_file=db_file, file_in=file_in)
    return updated_file

@router.put("/{file_id}/move", response_model=FileSchema)
def move_file(
    *,
    db: Session = Depends(get_db),
    file_id: uuid.UUID,
    file_in: FileMove,
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Move a file to a new folder.
    """
    db_file = crud_file.get_file(db=db, file_id=file_id, owner_id=current_user.id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found or access denied.")

    if file_in.parent_folder_id:
        target_folder = crud_folder.get_folder(db, folder_id=file_in.parent_folder_id, owner_id=current_user.id)
        if not target_folder:
            raise HTTPException(status_code=404, detail="Target folder not found or access denied.")
    
    updated_file = crud_file.move_file(db=db, db_file=db_file, file_in=file_in)
    return updated_file

@router.post("/upload/initiate", response_model=UploadSessionInitiateResponse)
def initiate_upload_session(
    *,
    db: Session = Depends(get_db),
    session_in: UploadSessionInitiateRequest,
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Initiate a chunked file upload session.
    """
    session = crud_upload_session.create_session(
        db=db, 
        filename=session_in.filename, 
        total_size=session_in.total_size, 
        owner=current_user
    )
    return {
        "session_token": session.session_token,
        "expires_at": session.expires_at
    }

@router.post("/upload/chunk", response_model=UploadChunkResponse)
def upload_chunk(
    *,
    db: Session = Depends(get_db),
    session_token: str = Form(...),
    file: UploadFile = FastAPIFile(...),
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Upload a single file chunk for a given session.
    """
    session = crud_upload_session.get_session_by_token(db, token=session_token, owner_id=current_user.id)
    if not session or session.status not in ['pending', 'uploading']:
        raise HTTPException(status_code=404, detail="Upload session not found or already completed.")

    try:
        with open(session.temp_file_path, "ab") as f:
            chunk_size = f.write(file.file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not write chunk: {e}")
    
    updated_session = crud_upload_session.update_session_size(db, db_session=session, chunk_size=chunk_size)
    
    return {
        "session_token": updated_session.session_token,
        "uploaded_size": updated_session.uploaded_size,
        "total_size": updated_session.total_size,
        "status": updated_session.status
    }

@router.post("/upload/complete", response_model=FileSchema)
def complete_upload_session(
    *,
    db: Session = Depends(get_db),
    session_token: str = Form(...),
    parent_folder_id: uuid.UUID | None = Form(None),
    current_user: UserModel = Depends(deps.get_current_user),
    storage_service: BaseStorageService = Depends(get_storage_service)
):
    session = crud_upload_session.get_session_by_token(db, token=session_token, owner_id=current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found.")
    
    if session.uploaded_size != session.total_size:
        raise HTTPException(status_code=400, detail="File upload is incomplete.")

    temp_path = Path(session.temp_file_path)
    sha256_hash = hashlib.sha256()
    with open(temp_path, "rb") as f:
        while chunk := f.read(8192):
            sha256_hash.update(chunk)
    file_hash = sha256_hash.hexdigest()

    saved_path, saved_filename = storage_service.save_from_path(
        source_path=temp_path,
        user_id=str(current_user.id),
        original_filename=session.filename
    )

    file_in = FileCreate(
        original_name=session.filename,
        filename=saved_filename,
        file_path=saved_path,
        size=session.total_size,
        mime_type="application/octet-stream",
        hash_sha256=file_hash,
        owner_id=current_user.id,
        parent_folder_id=parent_folder_id,
        upload_session_id=session.id
    )
    db_file = crud_file.create_file(db=db, file_in=file_in)
    crud_upload_session.complete_session(db, db_session=session)
    
    return db_file

@router.post("/{file_id}/share", response_model=Permission)
def share_file(
    *,
    db: Session = Depends(get_db),
    file_id: uuid.UUID,
    permission_in: PermissionCreate,
    current_user: UserModel = Depends(deps.get_current_user)
):
    """
    Share a file with another user.
    """
    db_file = crud_file.get_file(db, file_id=file_id, owner_id=current_user.id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found or you are not the owner.")
    
    permission = crud_permission.grant_permission(db, db_file=db_file, permission_in=permission_in, granter=current_user)
    if not permission:
        raise HTTPException(status_code=400, detail="Could not grant permission. Ensure user exists and is not yourself.")
        
    return permission