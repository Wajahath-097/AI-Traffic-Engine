"""
Vehicle search routes
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_
from app.database import get_db
from app.models.models import VehicleDetection, Camera, AuditLog
from app.schemas.schemas import VehicleDetectionResponse
from app.core.dependencies import get_current_traffic_officer, get_current_user
from app.models.models import User
from typing import List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/vehicles")
async def search_vehicles(
    plate: str = Query(None, max_length=50),
    camera_id: str = Query(None),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_traffic_officer),
    db: Session = Depends(get_db)
):
    """
    Search for vehicles by registration number or get all recent
    
    Supports exact and partial matching
    """
    from sqlalchemy import func
    
    query = db.query(VehicleDetection).order_by(desc(VehicleDetection.detected_at))
    
    normalized_plate = ''  # default for audit log when no plate is provided
    
    if plate:
        # Normalize plate for search
        normalized_plate = plate.upper().replace(" ", "")
        
        # Build query ignoring spaces in both the search string and the database column
        query = query.filter(or_(
            func.replace(VehicleDetection.plate_number, ' ', '').ilike(f"%{normalized_plate}%"),
            func.replace(VehicleDetection.ocr_normalized_text, ' ', '').ilike(f"%{normalized_plate}%")
        ))
    
    # Apply optional filters
    if camera_id:
        camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        if camera:
            query = query.filter(VehicleDetection.camera_id == camera.id)
    
    if start_date:
        query = query.filter(VehicleDetection.detected_at >= start_date)
    
    if end_date:
        query = query.filter(VehicleDetection.detected_at <= end_date)
    
    results = query.limit(limit).all()
    
    # Log search
    try:
        audit_log = AuditLog(
            user_id=current_user.id,
            action="vehicle_search",
            resource_type="vehicle",
            resource_id=normalized_plate or "all",
            details={
                "search_term": plate or "all",
                "results_count": len(results)
            }
        )
        db.add(audit_log)
        db.commit()
    except Exception:
        db.rollback()
    
    logger.info(f"Vehicle search by {current_user.officer_id}: {plate} - {len(results)} results")
    
    return {
        "plate": plate,
        "normalized_plate": normalized_plate,
        "results_count": len(results),
        "results": [
            {
                **VehicleDetectionResponse.from_orm(r).dict(),
                "camera_name": r.camera.name if r.camera else None,
                "camera_camera_id": r.camera.camera_id if r.camera else None
            } 
            for r in results
        ]
    }


@router.get("/vehicles/{detection_id}/history")
async def get_vehicle_history(
    detection_id: str,
    current_user: User = Depends(get_current_traffic_officer),
    db: Session = Depends(get_db)
):
    """
    Get complete detection history for a vehicle
    
    Shows all detections for the same plate
    """
    try:
        from uuid import UUID
        det_uuid = UUID(detection_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid detection ID format"
        )
    
    # Get the original detection
    original_detection = db.query(VehicleDetection).filter(VehicleDetection.id == det_uuid).first()
    if not original_detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )
    
    plate = original_detection.plate_number or original_detection.ocr_normalized_text
    if not plate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Detection has no plate number data"
        )
    
    # Get all detections for this plate
    history = db.query(VehicleDetection)\
        .filter(or_(
            VehicleDetection.plate_number == plate,
            VehicleDetection.ocr_normalized_text == plate
        ))\
        .order_by(desc(VehicleDetection.detected_at))\
        .all()
    
    # Log access
    audit_log = AuditLog(
        user_id=current_user.id,
        action="view_vehicle_history",
        resource_type="vehicle",
        resource_id=detection_id,
        details={"plate": plate}
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"Vehicle history viewed by {current_user.officer_id}: {plate}")
    
    return {
        "detection_id": detection_id,
        "plate": plate,
        "detection_count": len(history),
        "history": [VehicleDetectionResponse.from_orm(h) for h in history]
    }


@router.post("/vehicles/{detection_id}/flag")
async def flag_vehicle(
    detection_id: str,
    reason: str = Query(None),
    current_user: User = Depends(get_current_traffic_officer),
    db: Session = Depends(get_db)
):
    """
    Flag a vehicle for investigation (creates an alert)
    """
    try:
        from uuid import UUID
        det_uuid = UUID(detection_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid detection ID format"
        )
    
    detection = db.query(VehicleDetection).filter(VehicleDetection.id == det_uuid).first()
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )
    
    # Create an alert for this detection
    from app.models.models import Alert
    
    alert = Alert(
        severity="medium",
        alert_type="manual_flag",
        plate_number=detection.plate_number,
        camera_id=detection.camera_id,
        detection_id=detection.id,
        message=reason or "Flagged for investigation",
        status="open"
    )
    
    db.add(alert)
    db.commit()
    
    # Log flag
    audit_log = AuditLog(
        user_id=current_user.id,
        action="flag_vehicle",
        resource_type="vehicle",
        resource_id=detection_id,
        details={"reason": reason}
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"Vehicle flagged by {current_user.officer_id}: {detection.plate_number}")
    
    return {"message": "Vehicle flagged for investigation", "alert_id": str(alert.id)}
