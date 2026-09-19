"""
Camera management and monitoring routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Camera, CameraHealthEvent, AuditLog
from app.schemas.schemas import CameraCreate, CameraResponse, CameraUpdate, CameraHealthResponse
from app.core.dependencies import get_current_user, get_current_super_admin, get_current_control_room
from app.models.models import User
from typing import List
from datetime import datetime, timedelta
import logging
import cv2
import time

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[CameraResponse])
async def list_cameras(
    current_user: User = Depends(get_current_control_room),
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
    current_user: User = Depends(get_current_control_room),
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
    current_admin: User = Depends(get_current_super_admin),
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
    current_admin: User = Depends(get_current_super_admin),
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
    current_admin: User = Depends(get_current_super_admin),
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
    current_user: User = Depends(get_current_control_room),
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

from app.models.models import RegisteredVehicle, VehicleDetection

@router.get("/{camera_id}/stream")
async def stream_camera(camera_id: str):
    # Generator for MJPEG
    def generate_frames():
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
            if not camera:
                return
            # We don't strictly need the DB stream URL anymore because we use the standard HLS CDN
        finally:
            db.close()
            
        # As per integrator guide, HLS is the most reliable cross-network stream (e.g. cctv.corp8.cloud/cam01/index.m3u8)
        video_path = f"https://cctv.corp8.cloud/{camera_id}/index.m3u8"
        is_live_stream = True

        import os
        # HLS is HTTP based so it doesn't need TCP/UDP forcing, but a 5-second timeout is good
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "stimeout;5000000"
            
        # Use CAP_FFMPEG as per sentinel instructions
        cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            # Yield an offline frame if stream cannot be opened
            import numpy as np
            blank_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
            cv2.putText(blank_frame, f"STREAM {camera_id} OFFLINE", (300, 500), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 5)
            ret, buffer = cv2.imencode('.jpg', blank_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = buffer.tobytes()
            while True:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(1)
            return

        from app.ai.detection import get_yolo_detector
        try:
            yolo_detector = get_yolo_detector()
        except Exception:
            yolo_detector = None
            
        frame_count = 0
        last_detections = []

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    if is_live_stream:
                        time.sleep(1)
                        cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
                        continue
                    else:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                        
                # Resize frame for performance if it's 4K, but keep at 1080p for higher quality
                if frame.shape[1] > 1920:
                    frame = cv2.resize(frame, (1920, 1080))

                frame_count += 1
                
                if yolo_detector and frame_count % 10 == 0:
                    try:
                        last_detections = yolo_detector.detect_vehicles(frame)
                    except Exception as e:
                        logger.error(f"Detection error: {e}")
                        pass
                        
                for det in last_detections:
                    x1, y1, x2, y2 = map(int, det['bbox'])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    label = f"{det['class']} {det['confidence']:.2f}"
                    cv2.putText(frame, label, (x1, max(y1-5, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                frame_bytes = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                if not is_live_stream:
                    time.sleep(0.04)
        finally:
            if cap:
                cap.release()
            
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.get("/{camera_id}/live-detections")
async def get_live_detections(camera_id: str, db: Session = Depends(get_db)):
    """Get the latest real-time ML detections from the database"""
    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        return []
    
    # Get recent detections for this camera
    detections = db.query(VehicleDetection)\
        .filter(VehicleDetection.camera_id == camera.id)\
        .order_by(VehicleDetection.detected_at.desc())\
        .limit(10)\
        .all()
        
    return [
        {
            "id": str(d.id),
            "vehicle_class": d.vehicle_class,
            "vehicle_color": d.vehicle_color,
            "plate_number": d.plate_number if d.plate_confidence and d.plate_confidence > 0.90 else None,
            "confidence": round(d.confidence * 100, 1) if d.confidence else 0,
            "detected_at": d.detected_at.isoformat() + "Z"
        }
        for d in detections
    ]

from fastapi.responses import Response

@router.get("/{camera_id}/snapshot")
async def get_camera_snapshot(camera_id: str):
    """Get a single frame from the camera without running AI"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
    finally:
        db.close()
        
    # Use official HLS CDN endpoint
    video_path = f"https://cctv.corp8.cloud/{camera_id}/index.m3u8"

    import os
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "stimeout;5000000"
    cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        # Return offline frame if stream cannot be opened
        import numpy as np
        blank_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        cv2.putText(blank_frame, f"STREAM {camera_id} OFFLINE", (300, 500), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 5)
        ret, buffer = cv2.imencode('.jpg', blank_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return Response(content=buffer.tobytes(), media_type="image/jpeg")
        
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        import numpy as np
        blank_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        cv2.putText(blank_frame, f"NO FRAME FOR {camera_id}", (300, 500), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 5)
        ret, buffer = cv2.imencode('.jpg', blank_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return Response(content=buffer.tobytes(), media_type="image/jpeg")
        
    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    if not ret:
        raise HTTPException(status_code=500, detail="Could not encode frame")
        
    return Response(content=buffer.tobytes(), media_type="image/jpeg")

