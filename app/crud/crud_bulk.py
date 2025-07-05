from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID, uuid4
import os
import shutil
import hashlib
from pathlib import Path

from app.models import File, Folder, User
from app.schemas.bulk import BulkDeleteRequest, BulkMoveRequest, BulkCopyRequest
from . import crud_folder

def bulk_delete(db: Session, *, bulk_in: BulkDeleteRequest, owner_id: UUID) -> dict:
    """
    Performs a bulk deletion of files and folders owned by a user.
    """
    # --- File Deletion ---
    files_to_delete = db.query(File).filter(File.id.in_(bulk_in.file_ids), File.owner_id == owner_id).all()
    total_size_deleted = 0
    deleted_files_count = 0

    for file in files_to_delete:
        total_size_deleted += file.size
        file_path = Path(file.file_path)
        try:
            if file_path.is_file():
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file from storage: {e}") # Log this error
        db.delete(file)
        deleted_files_count += 1

    # --- Folder Deletion ---
    # This will delete the specified folders and rely on the database's
    # `ON DELETE CASCADE` to handle deleting sub-folders and files within them.
    # A more robust implementation would first query all descendants to delete
    # physical files and update user quota accurately.
    files_to_delete = db.query(File).filter(File.id.in_(bulk_in.file_ids), File.owner_id == owner_id).all()
    total_size_deleted = 0
    deleted_files_count = 0
    for file in files_to_delete:
        total_size_deleted += file.size
        file_path = Path(file.file_path)
        try:
            if file_path.is_file(): os.remove(file_path)
        except Exception as e: print(f"Error deleting file from storage: {e}")
        db.delete(file)
        deleted_files_count += 1
    folders_to_delete = db.query(Folder).filter(Folder.id.in_(bulk_in.folder_ids), Folder.owner_id == owner_id).all()
    deleted_folders_count = 0
    for folder in folders_to_delete:
        db.delete(folder)
        deleted_folders_count += 1
    if total_size_deleted > 0:
        db.query(User).filter(User.id == owner_id).update({User.used_storage: User.used_storage - total_size_deleted})
    db.commit()
    return {"deleted_files": deleted_files_count, "deleted_folders": deleted_folders_count}


def bulk_move(db: Session, *, bulk_in: BulkMoveRequest, owner_id: UUID) -> dict:
    """
    Performs a bulk move of files and folders.
    """
    ttarget_parent_path = "/"
    if bulk_in.target_parent_folder_id:
        target_folder = crud_folder.get_folder(db, folder_id=bulk_in.target_parent_folder_id, owner_id=owner_id)
        if not target_folder: return None
        target_parent_path = target_folder.path
    files_moved_count = db.query(File).filter(File.id.in_(bulk_in.file_ids), File.owner_id == owner_id).update({"parent_folder_id": bulk_in.target_parent_folder_id}, synchronize_session=False)
    folders_to_move = db.query(Folder).filter(Folder.id.in_(bulk_in.folder_ids), Folder.owner_id == owner_id).all()
    folders_moved_count = 0
    for folder in folders_to_move:
        old_path = folder.path
        new_path = f"{target_parent_path}/{folder.name}".replace("//", "/")
        db.query(Folder).filter(Folder.path.like(f"{old_path}/%")).update({Folder.path: func.replace(Folder.path, old_path, new_path)}, synchronize_session=False)
        folder.path = new_path
        folder.parent_folder_id = bulk_in.target_parent_folder_id
        db.add(folder)
        folders_moved_count += 1
    db.commit()
    return {"moved_files": files_moved_count, "moved_folders": folders_moved_count}

def bulk_copy(db: Session, *, bulk_in: BulkCopyRequest, owner: User) -> dict:
    """
    Performs a bulk copy of files and folders.
    """
    target_parent_path = "/"
    if bulk_in.target_parent_folder_id:
        target_folder = crud_folder.get_folder(db, folder_id=bulk_in.target_parent_folder_id, owner_id=owner.id)
        if not target_folder: return None
        target_parent_path = target_folder.path
    
    copied_files_count = 0
    copied_folders_count = 0
    total_size_copied = 0
    
    # --- File Copy ---
    files_to_copy = db.query(File).filter(File.id.in_(bulk_in.file_ids), File.owner_id == owner.id).all()
    for file in files_to_copy:
        new_file, new_size = _copy_file_instance(db, file, bulk_in.target_parent_folder_id, owner)
        if new_file:
            copied_files_count += 1
            total_size_copied += new_size

    # --- Folder Copy (Recursive) ---
    folders_to_copy = db.query(Folder).filter(Folder.id.in_(bulk_in.folder_ids), Folder.owner_id == owner.id).all()
    for folder in folders_to_copy:
        count, size = _copy_folder_recursive(db, folder, bulk_in.target_parent_folder_id, target_parent_path, owner)
        copied_folders_count += count
        total_size_copied += size

    # Update user quota
    if total_size_copied > 0:
        db.query(User).filter(User.id == owner.id).update(
            {User.used_storage: User.used_storage + total_size_copied}
        )
    
    db.commit()
    return {"copied_files": copied_files_count, "copied_folders": copied_folders_count}

def _copy_file_instance(db: Session, file_to_copy: File, target_parent_id: UUID, owner: User):
    """Helper to copy a single file instance."""
    source_path = Path(file_to_copy.file_path)
    if not source_path.is_file(): return None, 0

    user_storage_path = Path("./storage/local/files") / str(owner.id)
    user_storage_path.mkdir(parents=True, exist_ok=True)
    
    new_saved_filename = f"{uuid4()}{source_path.suffix}"
    dest_path = user_storage_path / new_saved_filename

    shutil.copy(source_path, dest_path)

    new_file = File(
        id=uuid4(),
        original_name=file_to_copy.original_name,
        filename=new_saved_filename,
        file_path=str(dest_path.relative_to(Path.cwd())),
        size=file_to_copy.size,
        mime_type=file_to_copy.mime_type,
        hash_sha256=f"{file_to_copy.hash_sha256}-{uuid4()}", # Ensure hash is unique
        owner_id=owner.id,
        parent_folder_id=target_parent_id
    )
    db.add(new_file)
    return new_file, new_file.size

def _copy_folder_recursive(db: Session, folder_to_copy: Folder, new_parent_id: UUID, new_parent_path: str, owner: User):
    """Helper to recursively copy a folder."""
    total_copied_folders = 0
    total_copied_size = 0

    # Create the new folder record
    new_folder_path = f"{new_parent_path}/{folder_to_copy.name}".replace("//", "/")
    new_folder = Folder(
        id=uuid4(),
        name=folder_to_copy.name,
        path=new_folder_path,
        parent_folder_id=new_parent_id,
        owner_id=owner.id
    )
    db.add(new_folder)
    total_copied_folders += 1

    # Copy files in the current folder
    for file in folder_to_copy.files:
        copied_file, copied_size = _copy_file_instance(db, file, new_folder.id, owner)
        if copied_file:
            total_copied_size += copied_size

    # Recursively copy subfolders
    for subfolder in folder_to_copy.subfolders:
        count, size = _copy_folder_recursive(db, subfolder, new_folder.id, new_folder.path, owner)
        total_copied_folders += count
        total_copied_size += size
        
    return total_copied_folders, total_copied_size
