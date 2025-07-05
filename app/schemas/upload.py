from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

# --- Initiate Session ---
class UploadSessionInitiateRequest(BaseModel):
    filename: str
    total_size: int

class UploadSessionInitiateResponse(BaseModel):
    session_token: str
    expires_at: datetime

# --- Upload Chunk ---
class UploadChunkResponse(BaseModel):
    session_token: str
    uploaded_size: int
    total_size: int
    status: str

# --- Complete Session ---
# We can reuse the existing File schema for the response.
# from .file import File as FileSchema
class UploadSessionCompleteResponse(BaseModel):
    session_token: str
    file_id: UUID
    filename: str
    total_size: int
    uploaded_size: int
    status: str
    created_at: datetime