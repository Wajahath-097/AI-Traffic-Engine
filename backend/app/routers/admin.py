"""
Administration and system management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.models.models import User, Role, AuditLog, BlacklistEntry, Camera, Alert, VehicleDetection
from app.schemas.schemas import UserCreate, UserResponse, BlacklistEntryCreate, BlacklistEntryResponse, AuditLogResponse, RoleResponse
from app.core.dependencies import get_current_admin, get_current_user
from app.core.security import hash_password
from typing import List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== User Management ====================

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all system users (admin only)
    """
    users = db.query(User).order_by(User.created_at).all()
    return [UserResponse.from_orm(u) for u in users]


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create new user account (admin only)
    """
    # Check if officer_id already exists
    existing = db.query(User).filter(User.officer_id == user_data.officer_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Officer ID already exists"
        )
    
    # Get role
    role = db.query(Role).filter(Role.id == user_data.role_id).first()
    if not role and user_data.role_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Hash password
    password_hash = hash_password(user_data.password)
    
    # Create user
    new_user = User(
        officer_id=user_data.officer_id,
        password_hash=password_hash,
        name=user_data.name,
        role_id=user_data.role_id,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log creation
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="create_user",
        resource_type="user",
        resource_id=str(new_user.id)
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"User created by {current_admin.officer_id}: {new_user.officer_id}")
    
    return UserResponse.from_orm(new_user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: dict,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update user information (admin only)
    """
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if "name" in user_data:
        user.name = user_data["name"]
    if "is_active" in user_data:
        user.is_active = user_data["is_active"]
    if "role_id" in user_data and user_data["role_id"]:
        role = db.query(Role).filter(Role.id == user_data["role_id"]).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        user.role_id = user_data["role_id"]
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"User updated by {current_admin.officer_id}: {user.officer_id}")
    
    return UserResponse.from_orm(user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete/deactivate user (admin only)
    """
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Deactivate instead of hard delete
    user.is_active = False
    db.commit()
    
    logger.info(f"User deactivated by {current_admin.officer_id}: {user.officer_id}")
    
    return {"message": "User has been deactivated"}


# ==================== Roles ====================

@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all available roles
    """
    roles = db.query(Role).all()
    return [RoleResponse.from_orm(r) for r in roles]


# ==================== Audit Logs ====================

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    user_id: str = Query(None),
    action: str = Query(None),
    limit: int = Query(100, le=1000),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get audit log entries (admin only)
    """
    query = db.query(AuditLog).order_by(desc(AuditLog.created_at))
    
    if user_id:
        try:
            from uuid import UUID
            user_uuid = UUID(user_id)
            query = query.filter(AuditLog.user_id == user_uuid)
        except ValueError:
            pass
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    logs = query.limit(limit).all()
    return [AuditLogResponse.from_orm(log) for log in logs]


# ==================== Blacklist Management ====================

@router.get("/blacklist", response_model=List[BlacklistEntryResponse])
async def get_blacklist(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get blacklisted vehicles
    """
    entries = db.query(BlacklistEntry)\
        .order_by(desc(BlacklistEntry.created_at))\
        .all()
    
    return [BlacklistEntryResponse.from_orm(e) for e in entries]


@router.post("/blacklist", response_model=BlacklistEntryResponse)
async def add_to_blacklist(
    entry_data: BlacklistEntryCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Add vehicle registration to blacklist (admin only)
    """
    # Check if already blacklisted
    existing = db.query(BlacklistEntry).filter(
        BlacklistEntry.plate_number == entry_data.plate_number
    ).first()
    
    if existing and (not existing.expires_at or existing.expires_at > datetime.utcnow()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"the numberplate entered that is already present in the blacklist"
        )
    
    # Create entry
    new_entry = BlacklistEntry(
        plate_number=entry_data.plate_number,
        reason=entry_data.reason,
        severity=entry_data.severity,
        created_by=current_admin.id,
        expires_at=entry_data.expires_at
    )
    
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    
    # Log action
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="add_to_blacklist",
        resource_type="blacklist",
        resource_id=entry_data.plate_number,
        details={"reason": entry_data.reason}
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"Vehicle added to blacklist by {current_admin.officer_id}: {entry_data.plate_number}")
    
    # Create alert for existing detections
    detections = db.query(VehicleDetection).filter(
        VehicleDetection.plate_number == entry_data.plate_number
    ).all()
    
    for detection in detections:
        alert = Alert(
            severity=entry_data.severity,
            alert_type="blacklist_match",
            plate_number=detection.plate_number,
            camera_id=detection.camera_id,
            detection_id=detection.id,
            message=f"Blacklisted vehicle detected: {entry_data.reason}",
            status="open"
        )
        db.add(alert)
    
    db.commit()
    
    return BlacklistEntryResponse.from_orm(new_entry)


@router.delete("/blacklist/{plate}")
async def remove_from_blacklist(
    plate: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Remove vehicle from blacklist (admin only)
    """
    entry = db.query(BlacklistEntry).filter(
        BlacklistEntry.plate_number == plate
    ).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle {plate} not found in blacklist"
        )
    
    db.delete(entry)
    db.commit()
    
    # Log action
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="remove_from_blacklist",
        resource_type="blacklist",
        resource_id=plate
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"Vehicle removed from blacklist by {current_admin.officer_id}: {plate}")
    
    return {"message": f"Vehicle {plate} removed from blacklist"}


# ==================== System Status ====================

@router.get("/system-status")
async def get_system_status(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get overall system status and metrics
    """
    # Count active cameras
    active_cameras = db.query(func.count(Camera.id))\
        .filter(Camera.enabled == True, Camera.status == "online")\
        .scalar() or 0
    
    total_cameras = db.query(func.count(Camera.id)).scalar() or 0
    
    # Count active users
    active_users = db.query(func.count(User.id))\
        .filter(User.is_active == True)\
        .scalar() or 0
    
    # Count alerts
    open_alerts = db.query(func.count(Alert.id))\
        .filter(Alert.status == "open")\
        .scalar() or 0
    
    from app.database import SessionLocal
    try:
        test_db = SessionLocal()
        test_db.execute("SELECT 1")
        database_status = "connected"
        test_db.close()
    except:
        database_status = "disconnected"
    
    return {
        "status": "healthy" if database_status == "connected" else "degraded",
        "database": database_status,
        "cameras": {
            "active": active_cameras,
            "total": total_cameras
        },
        "users": active_users,
        "open_alerts": open_alerts,
        "timestamp": datetime.utcnow().isoformat()
    }
