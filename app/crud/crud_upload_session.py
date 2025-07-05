from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from pathlib import Path
import secrets

from app.models.upload_session import UploadSession
from app.models.user import User

TEMP_STORAGE_PATH = Path("./storage/temp")

def create_session(db: Session, *, filename: str, total_size: int, owner: User) -> UploadSession:
    """
    Creates a new upload session.
    """
    TEMP_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    
    session_token = secrets.token_urlsafe(32)
    temp_file_path = TEMP_STORAGE_PATH / session_token
    expires_at = datetime.utcnow() + timedelta(hours=24) # Session expires in 24 hours

    db_session = UploadSession(
        user_id=owner.id,
        session_token=session_token,
        filename=filename,
        total_size=total_size,
        temp_file_path=str(temp_file_path),
        expires_at=expires_at
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session_by_token(db: Session, *, token: str, owner_id: UUID) -> UploadSession | None:
    """
    Gets an upload session by its token, ensuring ownership.
    """
    return db.query(UploadSession).filter(
        UploadSession.session_token == token, 
        UploadSession.user_id == owner_id
    ).first()

def update_session_size(db: Session, *, db_session: UploadSession, chunk_size: int) -> UploadSession:
    """
    Updates the uploaded size for a session.
    """
    db_session.uploaded_size += chunk_size
    db_session.status = "uploading"
    db.commit()
    db.refresh(db_session)
    return db_session

def complete_session(db: Session, *, db_session: UploadSession) -> UploadSession:
    """
    Marks an upload session as completed.
    """
    db_session.status = "completed"
    db.commit()
    db.refresh(db_session)
    return db_session
