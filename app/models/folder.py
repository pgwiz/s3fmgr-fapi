
import uuid
from sqlalchemy import Column, String, Text, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import TIMESTAMP
from app.core.database import Base

class Folder(Base):
    __tablename__ = "folders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    path = Column(Text, nullable=False, index=True)
    parent_folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="folders")
    parent_folder = relationship("Folder", remote_side=[id], back_populates="subfolders")
    subfolders = relationship("Folder", back_populates="parent_folder", cascade="all, delete-orphan")
    files = relationship("File", back_populates="parent_folder", cascade="all, delete-orphan")
