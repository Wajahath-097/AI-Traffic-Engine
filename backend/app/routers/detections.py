from fastapi import APIRouter, Depends
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import VehicleDetection
from app.schemas.schemas import VehicleDetectionResponse
from typing import List

router = APIRouter(prefix="/api/detections", tags=["detections"])

@router.get("/unique", response_model=List[VehicleDetectionResponse])
def get_unique_detections(db: Session = Depends(get_db)):
    """Return the most recent detection for each unique plate number."""
    subq = (
        db.query(
            VehicleDetection.plate_number,
            func.max(VehicleDetection.detected_at).label("max_at")
        )
        .group_by(VehicleDetection.plate_number)
        .subquery()
    )
    query = (
        db.query(VehicleDetection)
        .join(
            subq,
            (VehicleDetection.plate_number == subq.c.plate_number)
            & (VehicleDetection.detected_at == subq.c.max_at)
        )
    )
    return [VehicleDetectionResponse.from_orm(d) for d in query.all()]

@router.get("/with-camera", response_model=List[dict])
async def get_detections_with_camera(db: Session = Depends(get_db)):
    """Return detections including camera_id and camera_name for UI"""
    detections = (
        db.query(VehicleDetection)
        .options(joinedload(VehicleDetection.camera))
        .order_by(VehicleDetection.detected_at.desc())
        .limit(500)
        .all()
    )
    result = []
    for d in detections:
        result.append({
            "id": str(d.id),
            "plate_number": d.plate_number,
            "vehicle_class": d.vehicle_class,
            "vehicle_color": d.vehicle_color,
            "detected_at": d.detected_at.isoformat() if d.detected_at else None,
            "vehicle_confidence": d.vehicle_confidence,
            "camera_camera_id": d.camera.camera_id if d.camera else None,
            "camera_name": d.camera.name if d.camera else None,
            "camera_id": str(d.camera_id)
        })
    return result
