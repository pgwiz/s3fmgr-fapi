
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from uuid import UUID
from pathlib import Path
from app.services.storage_service import get_storage_service
from app.models.folder import Folder
from app.models.user import User
from app.schemas.folder import FolderCreate, FolderUpdate, FolderMove
from app.models.file import File
def get_folder(db: Session, *, folder_id: UUID, owner_id: UUID) -> Folder | None:
    """
    Fetches a folder by its ID, ensuring it belongs to the specified owner.

    Args:
        db: The database session.
        folder_id: The ID of the folder to fetch.
        owner_id: The ID of the user who owns the folder.

    Returns:
        The Folder object if found and owned by the user, otherwise None.
    """
    return db.query(Folder).filter(Folder.id == folder_id, Folder.owner_id == owner_id).first()


def create_folder(db: Session, *, folder_in: FolderCreate, owner: User) -> Folder:
    """
    Creates a new folder in the database.

    Args:
        db: The database session.
        folder_in: The folder creation schema.
        owner: The user who will own the folder.

    Returns:
        The newly created Folder object.
    """
    path = f"/{folder_in.name}"
    if folder_in.parent_folder_id:
        # Ensure the parent folder exists and belongs to the user
        parent_folder = get_folder(db, folder_id=folder_in.parent_folder_id, owner_id=owner.id)
        if parent_folder:
            path = f"{parent_folder.path}/{folder_in.name}"
        else:
            # Handle case where parent folder is not found or not owned by user
            return None 

    db_folder = Folder(
        name=folder_in.name,
        path=path,
        owner_id=owner.id,
        parent_folder_id=folder_in.parent_folder_id
    )

    db.add(db_folder)
    db.commit()
    db.refresh(db_folder)
    
    return db_folder

def rename_folder(db: Session, *, db_folder: Folder, folder_in: FolderUpdate) -> Folder:
    """
    Renames a folder and updates the paths of all its descendants.

    Args:
        db: The database session.
        db_folder: The folder object to update.
        folder_in: The schema with the new name.

    Returns:
        The updated Folder object.
    """
    old_path = db_folder.path
    new_name = folder_in.name
    
    # Construct the new path for the folder being renamed
    parent_path = str(Path(old_path).parent)
    new_path = f"{parent_path}/{new_name}".replace("//", "/") # Handle root case
    
    # Update the paths of all descendant folders
    # This query finds all folders whose path starts with the old path + "/"
    # and replaces that prefix with the new path + "/".
    db.query(Folder).filter(Folder.path.like(f"{old_path}/%")).update(
        {Folder.path: Folder.path.op('||')(new_path[len(old_path):])},
        synchronize_session=False
    )
    
    # Update the name and path of the target folder itself
    db_folder.name = new_name
    db_folder.path = new_path
    
    db.add(db_folder)
    db.commit()
    db.refresh(db_folder)
    
    return db_folder


def move_folder(db: Session, *, db_folder: Folder, new_parent_path: str, new_parent_id: UUID | None) -> Folder:
    """
    Moves a folder to a new location and updates paths of all descendants.

    Args:
        db: The database session.
        db_folder: The folder object to move.
        new_parent_path: The path of the new parent folder.
        new_parent_id: The ID of the new parent folder.

    Returns:
        The updated Folder object.
    """
    old_path = db_folder.path
    new_path = f"{new_parent_path}/{db_folder.name}".replace("//", "/")

    # Update paths of all descendant folders and files within them
    db.query(Folder).filter(Folder.path.like(f"{old_path}/%")).update(
        {Folder.path: func.replace(Folder.path, old_path, new_path)},
        synchronize_session=False
    )

    # Update the target folder itself
    db_folder.path = new_path
    db_folder.parent_folder_id = new_parent_id
    
    db.add(db_folder)
    db.commit()
    db.refresh(db_folder)

    return db_folder

def delete_folder(db: Session, *, folder_id: UUID, owner_id: UUID) -> bool:
    """
    Deletes a folder and all its contents (files and subfolders).
    """
    folder_to_delete = db.query(Folder).filter(Folder.id == folder_id, Folder.owner_id == owner_id).first()
    if not folder_to_delete:
        return False

    storage_service = get_storage_service()
    total_size_deleted = 0

    # Find all descendant folders, including the target one itself
    all_folders_to_delete = db.query(Folder).filter(Folder.path.like(f"{folder_to_delete.path}%"), Folder.owner_id == owner_id).all()
    folder_ids_to_delete = [f.id for f in all_folders_to_delete]

    # Find all files within these folders
    files_to_delete = db.query(File).filter(File.parent_folder_id.in_(folder_ids_to_delete)).all()

    # Delete physical files from storage and sum their sizes for quota update
    for file in files_to_delete:
        storage_service.delete(file.file_path)
        total_size_deleted += file.size

    # Delete the top-level folder from the database.
    # The `ondelete="CASCADE"` in the models will handle deleting all subfolder
    # and file records from the database.
    db.delete(folder_to_delete)

    # Update the user's storage quota
    if total_size_deleted > 0:
        db.query(User).filter(User.id == owner_id).update(
            {User.used_storage: User.used_storage - total_size_deleted}
        )
    
    db.commit()
    return True
