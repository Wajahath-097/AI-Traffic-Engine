"""
Vehicle detection and plate recognition routes
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.database import get_db
from app.models.models import VehicleDetection, Camera, AuditLog
from app.schemas.schemas import VehicleDetectionCreate, VehicleDetectionResponse
from app.core.dependencies import get_current_officer, get_current_user
from app.models.models import User
from typing import List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/detections", response_model=List[VehicleDetectionResponse])
async def get_detections(
    camera_id: str = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    """
    Get recent vehicle detections
    """
    query = db.query(VehicleDetection).order_by(desc(VehicleDetection.detected_at))
    
    if camera_id:
        # Verify camera exists
        camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera {camera_id} not found"
            )
        query = query.filter(VehicleDetection.camera_id == camera.id)
    
    detections = query.offset(offset).limit(limit).all()
    return [VehicleDetectionResponse.from_orm(d) for d in detections]


@router.get("/detections/{detection_id}", response_model=VehicleDetectionResponse)
async def get_detection(
    detection_id: str,
    current_user: User = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    """
    Get specific detection details with evidence
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
    
    # Log access to detection
    audit_log = AuditLog(
        user_id=current_user.id,
        action="view_detection",
        resource_type="detection",
        resource_id=detection_id
    )
    db.add(audit_log)
    db.commit()
    
    return VehicleDetectionResponse.from_orm(detection)


@router.post("/detections", response_model=VehicleDetectionResponse)
async def create_detection(
    detection_data: VehicleDetectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new vehicle detection (typically from AI pipeline)
    """
    # Verify camera exists
    camera = db.query(Camera).filter(Camera.id == detection_data.camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Create detection
    new_detection = VehicleDetection(
        camera_id=detection_data.camera_id,
        detected_at=detection_data.detected_at,
        vehicle_class=detection_data.vehicle_class,
        vehicle_confidence=detection_data.vehicle_confidence,
        plate_number=detection_data.plate_number,
        plate_confidence=detection_data.plate_confidence,
        ocr_raw_text=detection_data.ocr_raw_text,
        ocr_normalized_text=detection_data.ocr_normalized_text,
        ocr_engine=detection_data.ocr_engine,
        evidence_ref=detection_data.evidence_ref
    )
    
    db.add(new_detection)
    db.commit()
    db.refresh(new_detection)
    
    logger.info(f"Detection created: {new_detection.camera_id} - {new_detection.plate_number}")
    
    return VehicleDetectionResponse.from_orm(new_detection)


@router.get("/confidence-stats")
async def get_confidence_stats(
    hours: int = Query(24, le=720),
    current_user: User = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    """
    Get OCR confidence distribution statistics
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    detections = db.query(VehicleDetection)\
        .filter(VehicleDetection.created_at >= cutoff_time)\
        .filter(VehicleDetection.plate_confidence != None)\
        .all()
    
    if not detections:
        return {
            "total_recognitions": 0,
            "average_confidence": 0.0,
            "high_confidence_count": 0,
            "low_confidence_count": 0
        }
    
    confidences = [d.plate_confidence for d in detections if d.plate_confidence is not None]
    
    high_conf = sum(1 for c in confidences if c >= 0.8)
    low_conf = sum(1 for c in confidences if c < 0.5)
    
    return {
        "total_recognitions": len(confidences),
        "average_confidence": sum(confidences) / len(confidences) if confidences else 0,
        "high_confidence_count": high_conf,
        "low_confidence_count": low_conf,
        "confidence_distribution": {
            "0.0-0.3": sum(1 for c in confidences if c < 0.3),
            "0.3-0.5": sum(1 for c in confidences if 0.3 <= c < 0.5),
            "0.5-0.7": sum(1 for c in confidences if 0.5 <= c < 0.7),
            "0.7-0.9": sum(1 for c in confidences if 0.7 <= c < 0.9),
            "0.9-1.0": sum(1 for c in confidences if c >= 0.9)
        }
    }
