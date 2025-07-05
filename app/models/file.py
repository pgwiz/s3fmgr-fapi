
import uuid
from sqlalchemy import Column, String, Text, BigInteger, Float, Boolean, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import TIMESTAMP
from app.core.database import Base

class File(Base):
    __tablename__ = "files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    cloud_path = Column(Text, nullable=True)
    size = Column(BigInteger, nullable=False)
    mime_type = Column(String(255), nullable=False)
    hash_sha256 = Column(String(64), unique=True, index=True, nullable=False)
    parent_folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    upload_session_id = Column(UUID(as_uuid=True), ForeignKey("upload_sessions.id"), nullable=True)
    is_encrypted = Column(Boolean, default=False)
    compression_ratio = Column(Float, nullable=True)
    thumbnail_path = Column(Text, nullable=True)
    virus_scan_status = Column(String(50), default='pending')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="files")
    parent_folder = relationship("Folder", back_populates="files")
    upload_session = relationship("UploadSession")
    permissions = relationship("FilePermission", back_populates="file", cascade="all, delete-orphan")
