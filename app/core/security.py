from datetime import datetime, timedelta, timezone
from typing import Any, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# A CryptContext for hashing passwords.

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """

    Verifies a plain-text password against a hashed password.
    
    Args:
        plain_password: The password to verify.
        hashed_password: The stored hash to compare against.
        
    Returns:
        True if the password is correct, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hashes a plain-text password.
    
    Args:
        password: The password to hash.
        
    Returns:
        The resulting password hash.
    """
    return pwd_context.hash(password)

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """
    Creates a JWT access token.

    Args:
        subject: The subject of the token (e.g., user ID or email).
        expires_delta: The lifespan of the token.

    Returns:
        The encoded JWT token as a string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
