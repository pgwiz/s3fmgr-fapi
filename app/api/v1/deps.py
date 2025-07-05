# It holds reusable dependencies for our API endpoints, like getting the current user.

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.core.database import get_db
from app.core.config import settings
from app.schemas.user import TokenData
from app.crud import crud_user
from app.models.user import User

# This scheme will look for a token in the "Authorization" header
# with the value "Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to get the current user from a JWT token.
    
    Decodes the token, validates its signature and expiration,
    and fetches the corresponding user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = crud_user.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    

    return user