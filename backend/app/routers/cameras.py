"""
Camera management and monitoring routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Camera, CameraHealthEvent, AuditLog
from app.schemas.schemas import CameraCreate, CameraResponse, CameraUpdate, CameraHealthResponse
from app.core.dependencies import get_current_user, get_current_admin, get_current_officer
from app.models.models import User
from typing import List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[CameraResponse])
async def list_cameras(
    current_user: User = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    """
    Get all configured cameras
    """
    cameras = db.query(Camera).order_by(Camera.camera_id).all()
    return [CameraResponse.from_orm(cam) for cam in cameras]


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: str,
    current_user: User = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    """
    Get specific camera details and status
    """
    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )
    
    # Log access
    audit_log = AuditLog(
        user_id=current_user.id,
        action="view_camera",
        resource_type="camera",
        resource_id=str(camera.id)
    )
    db.add(audit_log)
    db.commit()
    
    return CameraResponse.from_orm(camera)


@router.post("/", response_model=CameraResponse)
async def create_camera(
    camera_data: CameraCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Add a new camera (admin only)
    """
    # Check if camera_id already exists
    existing = db.query(Camera).filter(Camera.camera_id == camera_data.camera_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Camera {camera_data.camera_id} already exists"
        )
    
    # Create camera
    new_camera = Camera(
        camera_id=camera_data.camera_id,
        name=camera_data.name,
        location=camera_data.location,
        latitude=camera_data.latitude,
        longitude=camera_data.longitude,
        protocol=camera_data.protocol,
        stream_secret_ref=camera_data.stream_secret_ref,
        enabled=camera_data.enabled,
        status="unknown"
    )
    
    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)
    
    # Log creation
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="create_camera",
        resource_type="camera",
        resource_id=str(new_camera.id),
        details={"camera_id": camera_data.camera_id}
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"Camera created: {new_camera.camera_id}")
    
    return CameraResponse.from_orm(new_camera)


@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: str,
    camera_data: CameraUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update camera configuration (admin only)
    """
    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )
    
    # Update fields
    if camera_data.name is not None:
        camera.name = camera_data.name
    if camera_data.location is not None:
        camera.location = camera_data.location
    if camera_data.latitude is not None:
        camera.latitude = camera_data.latitude
    if camera_data.longitude is not None:
        camera.longitude = camera_data.longitude
    if camera_data.enabled is not None:
        camera.enabled = camera_data.enabled
    if camera_data.status is not None:
        camera.status = camera_data.status
    
    camera.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(camera)
    
    # Log update
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="update_camera",
        resource_type="camera",
        resource_id=str(camera.id)
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"Camera updated: {camera.camera_id}")
    
    return CameraResponse.from_orm(camera)


@router.delete("/{camera_id}")
async def delete_camera(
    camera_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete/disable a camera (admin only)
    """
    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )
    
    # Disable instead of hard delete to preserve history
    camera.enabled = False
    camera.updated_at = datetime.utcnow()
    db.commit()
    
    # Log deletion
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="delete_camera",
        resource_type="camera",
        resource_id=str(camera.id)
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"Camera disabled: {camera.camera_id}")
    
    return {"message": f"Camera {camera_id} has been disabled"}


@router.get("/{camera_id}/health", response_model=List[CameraHealthResponse])
async def get_camera_health(
    camera_id: str,
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    """
    Get camera stream health and status (recent events)
    """
    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )
    
    # Get recent health events
    health_events = db.query(CameraHealthEvent)\
        .filter(CameraHealthEvent.camera_id == camera.id)\
        .order_by(CameraHealthEvent.recorded_at.desc())\
        .limit(limit)\
        .all()
    
    return [CameraHealthResponse.from_orm(event) for event in health_events]


@router.post("/{camera_id}/health")
async def record_camera_health(
    camera_id: str,
    status: str,
    latency_ms: int = None,
    error_code: str = None,
    message: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Record camera health event (internal use, from camera worker)
    """
    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )
    
    # Create health event
    health_event = CameraHealthEvent(
        camera_id=camera.id,
        status=status,
        latency_ms=latency_ms,
        error_code=error_code,
        message=message
    )
    
    # Update camera status
    camera.status = status
    camera.last_heartbeat = datetime.utcnow()
    
    db.add(health_event)
    db.commit()
    
    return {"message": "Health event recorded"}

from fastapi.responses import StreamingResponse
import cv2
import time
import os
from app.ai.detection import get_yolo_detector, get_ocr_engine
from app.models.models import RegisteredVehicle

LIVE_DETECTIONS = {}

@router.get("/{camera_id}/stream")
async def stream_camera(camera_id: str, db: Session = Depends(get_db)):
    # Generator for MJPEG
    def generate_frames():
        camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        if not camera:
            return
            
        video_map = {
            "CAM-001": "13020032_3840_2160_30fps.mp4",
            "CAM-002": "13105476_3840_2160_30fps.mp4",
            "CAM-003": "14985169_1920_1080_25fps.mp4"
        }
        video_file = video_map.get(camera_id, "13020032_3840_2160_30fps.mp4")
        
        from pathlib import Path
        backend_dir = Path(__file__).resolve().parent.parent.parent
        video_path = str(backend_dir.parent / "media" / "offline_videos" / video_file)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return
            
        detector = get_yolo_detector()
        ocr = get_ocr_engine()
        
        frame_count = 0
        last_boxes = []
        
        if camera_id not in LIVE_DETECTIONS:
            LIVE_DETECTIONS[camera_id] = []
            
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
                
            frame_count += 1
            
            # Process every 5th frame to save CPU
            if frame_count % 5 == 0:
                small_frame = cv2.resize(frame, (1280, 720))
                detections = detector.detect_vehicles(small_frame, confidence_threshold=0.4)
                
                current_boxes = []
                recent_live_dets = []
                
                for det in detections:
                    bbox = det["bbox"]
                    v_class = det["class"]
                    
                    plate_region = detector.detect_plates(small_frame, bbox)
                    plate_text = ""
                    if plate_region:
                        ocr_res = ocr.recognize_plate(small_frame, plate_region["bbox"])
                        if ocr_res and ocr_res.get("normalized_text"):
                            plate_text = ocr_res.get("normalized_text")
                            if "MOCKPLATE" in plate_text:
                                plate_text = ""
                    
                    color = "unknown"
                    status = "UNVERIFIED"
                    if plate_text:
                        color = detector.detect_color(small_frame, bbox)
                        # Check RTO Database
                        rto_record = db.query(RegisteredVehicle).filter(RegisteredVehicle.plate_number == plate_text).first()
                        if rto_record:
                            # Verify class (YOLO class vs RTO class) and color
                            if rto_record.vehicle_class.lower() == v_class.lower():
                                status = "VERIFIED"
                            else:
                                status = "MISMATCH"
                        else:
                            status = "NOT_FOUND"
                            
                        # Cloud evidence mock URL
                        cloud_url = f"s3://traffic-evidence-bucket/{camera_id}_{plate_text}_{int(time.time())}.jpg"
                            
                        det_info = {
                            "id": f"{plate_text}_{int(time.time())}",
                            "plate_number": plate_text,
                            "vehicle_class": v_class,
                            "vehicle_color": color,
                            "confidence": round(det["confidence"] * 100, 1),
                            "verification_status": status,
                            "detected_at": datetime.utcnow().isoformat() + "Z",
                            "evidence_url": cloud_url
                        }
                        recent_live_dets.append(det_info)
                        
                    current_boxes.append((bbox, v_class, plate_text, det["confidence"], status))
                    
                last_boxes = current_boxes
                if recent_live_dets:
                    # Prepend newest detections, keep max 10
                    LIVE_DETECTIONS[camera_id] = (recent_live_dets + LIVE_DETECTIONS[camera_id])[:10]
                    
                draw_frame = small_frame
            else:
                draw_frame = cv2.resize(frame, (1280, 720))
                
            # Draw boxes
            for bbox, v_class, plate_text, conf, status in last_boxes:
                x1, y1, x2, y2 = map(int, bbox)
                
                box_color = (0, 255, 0) # Green for verified/unverified
                if status == "MISMATCH":
                    box_color = (0, 0, 255) # Red for mismatch
                    
                cv2.rectangle(draw_frame, (x1, y1), (x2, y2), box_color, 2)
                label = f"{v_class} {conf:.2f}"
                if plate_text:
                    label += f" [{plate_text}]"
                cv2.putText(draw_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
                
            ret, buffer = cv2.imencode('.jpg', draw_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                   
            time.sleep(0.04)
            
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.get("/{camera_id}/live-detections")
async def get_live_detections(camera_id: str):
    """Get the latest real-time ML detections from the video stream"""
    return LIVE_DETECTIONS.get(camera_id, [])

