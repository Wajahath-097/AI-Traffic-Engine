"""
Vehicle trajectory and journey routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.models import Journey, JourneyEvent, VehicleDetection, Camera, AuditLog
from app.schemas.schemas import JourneyResponse, JourneyEventResponse
from app.core.dependencies import get_current_traffic_officer, get_current_user
from app.models.models import User
from typing import List
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[JourneyResponse])
@router.get("/journeys", response_model=List[JourneyResponse])
async def list_trajectories(
    limit: int = Query(50, le=1000),
    current_user: User = Depends(get_current_traffic_officer),
    db: Session = Depends(get_db)
):
    """
    Get list of recent trajectories
    """
    journeys = db.query(Journey)\
        .order_by(desc(Journey.created_at))\
        .limit(limit)\
        .all()
    
    return [JourneyResponse.from_orm(j) for j in journeys]


@router.get("/map-data")
async def get_general_map_data(
    current_user: User = Depends(get_current_traffic_officer),
    db: Session = Depends(get_db)
):
    """
    Get GIS GeoJSON for all active cameras
    """
    cameras = db.query(Camera).filter(Camera.enabled == True).all()
    features = []
    for camera in cameras:
        if camera.latitude and camera.longitude:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [camera.longitude, camera.latitude]
                },
                "properties": {
                    "type": "camera",
                    "camera_id": camera.camera_id,
                    "name": camera.name,
                    "location": camera.location,
                    "status": camera.status
                }
            })
    return {
        "geojson": {
            "type": "FeatureCollection",
            "features": features
        }
    }


@router.get("/{trajectory_id}", response_model=JourneyResponse)
async def get_trajectory(
    trajectory_id: str,
    current_user: User = Depends(get_current_traffic_officer),
    db: Session = Depends(get_db)
):
    """
    Get specific trajectory with all journey events
    """
    try:
        from uuid import UUID
        traj_uuid = UUID(trajectory_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid trajectory ID format"
        )
    
    journey = db.query(Journey).filter(Journey.id == traj_uuid).first()
    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trajectory not found"
        )
    
    # Log access
    audit_log = AuditLog(
        user_id=current_user.id,
        action="view_trajectory",
        resource_type="trajectory",
        resource_id=trajectory_id
    )
    db.add(audit_log)
    db.commit()
    
    return JourneyResponse.from_orm(journey)


@router.post("/reconstruct")
async def reconstruct_trajectory(
    plate: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_traffic_officer),
    db: Session = Depends(get_db)
):
    """
    Reconstruct trajectory for a vehicle registration
    
    Matches detections across cameras and creates a journey
    """
    # Normalize plate
    normalized_plate = plate.upper().replace(" ", "")
    
    # Find all detections for this plate
    detections = db.query(VehicleDetection)\
        .filter(VehicleDetection.plate_number == normalized_plate)\
        .order_by(VehicleDetection.detected_at)\
        .all()
    
    if not detections:
        return {
            "plate": plate,
            "normalized_plate": normalized_plate,
            "trajectory": None,
            "message": "No detections found for this plate"
        }
    
    # Check if journey already exists
    existing_journey = db.query(Journey)\
        .filter(Journey.plate_number == normalized_plate)\
        .first()
    
    if existing_journey:
        # Update existing journey
        journey = existing_journey
        journey.end_time = detections[-1].detected_at
        journey.confidence = sum(d.plate_confidence for d in detections if d.plate_confidence) / len(detections)
    else:
        # Create new journey
        journey = Journey(
            plate_number=normalized_plate,
            start_time=detections[0].detected_at,
            end_time=detections[-1].detected_at,
            confidence=sum(d.plate_confidence for d in detections if d.plate_confidence) / len(detections),
            start_camera_id=detections[0].camera_id,
            end_camera_id=detections[-1].camera_id
        )
        db.add(journey)
    
    db.commit()
    db.refresh(journey)
    
    # Create/update journey events
    db.query(JourneyEvent).filter(JourneyEvent.journey_id == journey.id).delete()
    
    for idx, detection in enumerate(detections):
        journey_event = JourneyEvent(
            journey_id=journey.id,
            detection_id=detection.id,
            sequence_number=idx + 1
        )
        db.add(journey_event)
    
    db.commit()
    db.refresh(journey)
    
    # Log trajectory reconstruction
    audit_log = AuditLog(
        user_id=current_user.id,
        action="reconstruct_trajectory",
        resource_type="trajectory",
        resource_id=str(journey.id),
        details={"plate": plate, "detection_count": len(detections)}
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"Trajectory reconstructed for {plate} by {current_user.officer_id}: {len(detections)} detections")
    
    return {
        "plate": plate,
        "normalized_plate": normalized_plate,
        "trajectory": JourneyResponse.from_orm(journey),
        "detection_count": len(detections)
    }


@router.get("/{trajectory_id}/map-data")
async def get_trajectory_map_data(
    trajectory_id: str,
    current_user: User = Depends(get_current_traffic_officer),
    db: Session = Depends(get_db)
):
    """
    Get GIS-compatible data for trajectory visualization (GeoJSON)
    """
    try:
        from uuid import UUID
        traj_uuid = UUID(trajectory_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid trajectory ID format"
        )
    
    journey = db.query(Journey).filter(Journey.id == traj_uuid).first()
    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trajectory not found"
        )
    
    # Get journey events with detection details
    journey_events = db.query(JourneyEvent, VehicleDetection)\
        .join(VehicleDetection)\
        .filter(JourneyEvent.journey_id == journey.id)\
        .order_by(JourneyEvent.sequence_number)\
        .all()
    
    # Get camera locations
    camera_ids = set()
    for event, detection in journey_events:
        camera_ids.add(detection.camera_id)
    
    cameras = db.query(Camera).filter(Camera.id.in_(camera_ids)).all() if camera_ids else []
    camera_map = {cam.id: cam for cam in cameras}
    
    # Build GeoJSON
    features = []
    
    # Add camera locations as points
    for camera in cameras:
        if camera.latitude and camera.longitude:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [camera.longitude, camera.latitude]
                },
                "properties": {
                    "type": "camera",
                    "camera_id": camera.camera_id,
                    "name": camera.name,
                    "location": camera.location
                }
            })
    
    # Add detection points along trajectory
    coordinates = []
    for event, detection in journey_events:
        camera = camera_map.get(detection.camera_id)
        if camera and camera.latitude and camera.longitude:
            coordinates.append([camera.longitude, camera.latitude])
            
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [camera.longitude, camera.latitude]
                },
                "properties": {
                    "type": "detection",
                    "sequence": event.sequence_number,
                    "timestamp": detection.detected_at.isoformat(),
                    "camera_id": camera.camera_id,
                    "plate": detection.plate_number,
                    "confidence": detection.plate_confidence
                }
            })
    
    # Add trajectory line
    if len(coordinates) > 1:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            },
            "properties": {
                "type": "trajectory",
                "plate": journey.plate_number,
                "confidence": journey.confidence
            }
        })
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return {
        "trajectory_id": trajectory_id,
        "plate": journey.plate_number,
        "geojson": geojson
    }
