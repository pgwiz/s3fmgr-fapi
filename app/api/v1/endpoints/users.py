from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.user import User
from app.api.v1 import deps

router = APIRouter()

@router.get("/me", response_model=User)
def read_users_me(
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get current user.
    
    This endpoint is protected and requires a valid JWT token.
    It returns the details of the currently authenticated user.
    """
    return current_user
