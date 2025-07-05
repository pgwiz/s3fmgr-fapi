from sqlalchemy.orm import Session
from uuid import UUID

from app.models import File, User, FilePermission
from app.schemas.permission import PermissionCreate
from . import crud_user

def grant_permission(db: Session, *, db_file: File, permission_in: PermissionCreate, granter: User) -> FilePermission | None:
    """
    Grants a permission on a file to another user.
    """
    # Find the user to grant permission to
    target_user = crud_user.get_user_by_email(db, email=permission_in.user_email)
    if not target_user or target_user.id == granter.id:
        return None # Cannot grant to non-existent user or self

    # Check if permission already exists
    existing_perm = db.query(FilePermission).filter(
        FilePermission.file_id == db_file.id,
        FilePermission.user_id == target_user.id
    ).first()

    if existing_perm:
        # Update existing permission
        existing_perm.permission_type = permission_in.permission_type
        existing_perm.expires_at = permission_in.expires_at
        db.add(existing_perm)
    else:
        # Create new permission
        new_perm = FilePermission(
            file_id=db_file.id,
            user_id=target_user.id,
            permission_type=permission_in.permission_type.value,
            granted_by=granter.id,
            expires_at=permission_in.expires_at
        )
        db.add(new_perm)
    
    db.commit()
    return existing_perm or new_perm

def has_read_permission(db: Session, *, db_file: File, user: User) -> bool:
    """
    Checks if a user has read permission for a file (either as owner or via a share).
    """
    if db_file.owner_id == user.id:
        return True
    
    permission = db.query(FilePermission).filter(
        FilePermission.file_id == db_file.id,
        FilePermission.user_id == user.id,
        FilePermission.permission_type.in_(['read', 'write'])
    ).first()

    return permission is not None
