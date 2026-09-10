"""
Security utilities for JWT and password management
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class TokenData(BaseModel):
    """Token payload data"""
    officer_id: str
    user_id: str
    role: str
    exp: datetime


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    pwd_bytes = password.encode('utf-8')
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    pwd_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(
    officer_id: str,
    user_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token
    
    Args:
        officer_id: Officer's ID
        user_id: User UUID
        role: User's role
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = {
        "officer_id": officer_id,
        "user_id": user_id,
        "role": role
    }
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating JWT token: {e}")
        raise


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        officer_id: str = payload.get("officer_id")
        user_id: str = payload.get("user_id")
        role: str = payload.get("role")
        
        if officer_id is None or user_id is None:
            return None
            
        token_data = TokenData(
            officer_id=officer_id,
            user_id=user_id,
            role=role,
            exp=datetime.fromtimestamp(payload.get("exp"))
        )
        return token_data
        
    except JWTError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None
