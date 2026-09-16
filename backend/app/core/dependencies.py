"""
FastAPI dependencies for authentication and authorization
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import verify_token
from app.models.models import User
import logging
import uuid

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token
    """
    token = credentials.credentials
    
    token_data = verify_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    try:
        user_uuid = uuid.UUID(token_data.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify current user has 'Super Admin' role (Full system administration)
    """
    if current_user.role is None or current_user.role.name != "Super Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have Super Admin privileges"
        )
    return current_user


async def get_current_traffic_officer(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify current user has 'Traffic Officer' role or higher
    (Assigned cameras + vehicle searches)
    """
    allowed_roles = ["Traffic Officer", "Super Admin"]
    if current_user.role is None or current_user.role.name not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have Traffic Officer privileges"
        )
    return current_user


async def get_current_control_room(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify current user has 'Control Room' role or higher
    (Live feeds + alerts)
    """
    allowed_roles = ["Control Room", "Super Admin"]
    if current_user.role is None or current_user.role.name not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have Control Room privileges"
        )
    return current_user


async def get_current_analyst(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify current user has 'Analyst' role or higher
    (Reports/statistics)
    """
    allowed_roles = ["Analyst", "Super Admin"]
    if current_user.role is None or current_user.role.name not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have Analyst privileges"
        )
    return current_user


async def get_current_auditor(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify current user has 'Auditor' role or higher
    (Logs only)
    """
    allowed_roles = ["Auditor", "Super Admin"]
    if current_user.role is None or current_user.role.name not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have Auditor privileges"
        )
    return current_user
