
import uuid
from sqlalchemy import Column, String, BigInteger, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import TIMESTAMP
from app.core.database import Base

class UploadSession(Base):
    __tablename__ = "upload_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_token = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    total_size = Column(BigInteger, nullable=False)
    uploaded_size = Column(BigInteger, default=0)
    temp_file_path = Column(String, nullable=False)
    status = Column(String(50), default='pending')
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    owner = relationship("User")
