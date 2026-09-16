"""
Authentication routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, Role
from app.schemas.schemas import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.core.security import hash_password, create_access_token
from app.core.dependencies import get_current_user, get_current_super_admin
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Officer login endpoint
    
    Returns JWT token on successful authentication
    """
    # Find user by officer_id
    user = db.query(User).filter(User.officer_id == request.officer_id).first()
    
    if not user:
        # Don't reveal if user exists or not for security
        logger.warning(f"Login attempt with non-existent officer_id: {request.officer_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        logger.warning(f"Login attempt with inactive user: {user.officer_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Verify password
    from app.core.security import verify_password
    if not verify_password(request.password, user.password_hash):
        logger.warning(f"Failed login attempt for user: {user.officer_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Update last login timestamp
    from datetime import datetime
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create access token
    role_name = user.role.name if user.role else "officer"
    access_token = create_access_token(
        officer_id=user.officer_id,
        user_id=str(user.id),
        role=role_name,
        expires_delta=timedelta(hours=24)
    )
    
    # Log login
    from app.models.models import AuditLog
    audit_log = AuditLog(
        user_id=user.id,
        action="login",
        resource_type="user",
        resource_id=str(user.id)
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"Successful login: {user.officer_id}")
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.from_orm(user)
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Officer logout endpoint
    
    Note: JWT is stateless, this logs the event but doesn't invalidate the token
    Token invalidation typically requires token blacklisting in production
    """
    # Log logout event
    from app.models.models import AuditLog
    audit_log = AuditLog(
        user_id=current_user.id,
        action="logout",
        resource_type="user",
        resource_id=str(current_user.id)
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"Logout: {current_user.officer_id}")
    
    return {"message": "Logged out successfully"}


@router.post("/register", response_model=UserResponse)
async def register(
    user_create: UserCreate,
    current_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """
    Register new officer (admin only)
    
    Creates a new user account in the system
    """
    # Check if officer_id already exists
    existing_user = db.query(User).filter(User.officer_id == user_create.officer_id).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Officer ID already exists"
        )
    
    # Get role
    role = db.query(Role).filter(Role.id == user_create.role_id).first()
    if not role and user_create.role_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Hash password
    password_hash = hash_password(user_create.password)
    
    # Create new user
    new_user = User(
        officer_id=user_create.officer_id,
        password_hash=password_hash,
        name=user_create.name,
        role_id=user_create.role_id or role.id if role else None,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log user creation
    from app.models.models import AuditLog
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="create_user",
        resource_type="user",
        resource_id=str(new_user.id)
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"New user registered: {new_user.officer_id}")
    
    return UserResponse.from_orm(new_user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    """
    return UserResponse.from_orm(current_user)
