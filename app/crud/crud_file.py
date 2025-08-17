from sqlalchemy.orm import Session
from uuid import UUID
import os
from app.services.storage_service import get_storage_service
from app.models.file import File
from app.models.user import User
from app.schemas.file import FileCreate, FileUpdate, FileMove
from pathlib import Path


def set_public_status(db: Session, *, db_file: File, is_public: bool) -> File:
    """Updates the public status of a file in the database."""
    db_file.is_public = is_public
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_file_by_id(db: Session, *, file_id: UUID) -> File | None:
    """
    Fetches a file by its ID, without checking for ownership.
    """
    return db.query(File).filter(File.id == file_id).first()

def get_file(db: Session, *, file_id: UUID, owner_id: UUID) -> File | None:
    """
    Fetches a file by its ID, ensuring it belongs to the specified owner.

    Args:
        db: The database session.
        file_id: The ID of the file to fetch.
        owner_id: The ID of the user who owns the file.

    Returns:
        The File object if found and owned by the user, otherwise None.
    """
    return db.query(File).filter(File.id == file_id, File.owner_id == owner_id).first()


def create_file(db: Session, *, file_in: FileCreate) -> File:
    """
    Creates a new file record in the database and updates user storage.

    Args:
        db: The database session.
        file_in: The file creation schema.

    Returns:
        The newly created File object.
    """
    # Create the new File model instance
    db_file = File(**file_in.model_dump())
    
    # Add, commit, and refresh
    db.add(db_file)
    
    # Atomically update the user's used storage
    db.query(User).filter(User.id == file_in.owner_id).update(
        {User.used_storage: User.used_storage + file_in.size}
    )
    
    db.commit()
    db.refresh(db_file)
    
    return db_file

def delete_file(db: Session, *, file_id: UUID, owner_id: UUID) -> File | None:
    db_file = get_file(db=db, file_id=file_id, owner_id=owner_id)
    if not db_file:
        return None

    # Get storage service and delete the physical file
    storage_service = get_storage_service()
    storage_service.delete(file_path=db_file.file_path)
    """
    Deletes a file from the database and storage, and updates user quota.

    Args:
        db: The database session.
        file_id: The ID of the file to delete.
        owner_id: The ID of the user who owns the file.

    Returns:
        The deleted File object if found, otherwise None.
    """
    # Get the file to ensure it exists and belongs to the user
    db_file = get_file(db=db, file_id=file_id, owner_id=owner_id)
    if not db_file:
        return None

    # Delete the physical file from storage
    file_path = Path(db_file.file_path)
    try:
        if file_path.is_file():
            os.remove(file_path)
    except Exception as e:
        # Log the error, but don't block the DB operation
        print(f"Error deleting file from storage: {e}")

    db.query(User).filter(User.id == owner_id).update({User.used_storage: User.used_storage - db_file.size})
    db.delete(db_file)
    db.commit()
    return db_file


def rename_file(db: Session, *, db_file: File, file_in: FileUpdate) -> File:
    """
    Renames a file.

    Args:
        db: The database session.
        db_file: The file object to update.
        file_in: The schema with the new name.

    Returns:
        The updated File object.
    """
    db_file.original_name = file_in.original_name
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def move_file(db: Session, *, db_file: File, file_in: FileMove) -> File:
    """
    Moves a file to a new parent folder.

    Args:
        db: The database session.
        db_file: The file object to move.
        file_in: The schema with the new parent folder ID.

    Returns:
        The updated File object.
    """
    db_file.parent_folder_id = file_in.parent_folder_id
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file
