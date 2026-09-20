"""
Camera management and monitoring routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse, Response
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
import threading
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/ingest")
def get_ingest_catalogue(db: Session = Depends(get_db)):
    """
    Sentinel Sandbox Ingest Catalogue: Returns all cameras with stream URLs
    """
    try:
        from app.core.config import settings
        cameras = db.query(Camera).order_by(Camera.camera_id).all()
        stream_host = getattr(settings, "STREAM_HOST", "103.250.160.189")
        email = settings.STREAM_EMAIL.replace("@", "%40") if getattr(settings, "STREAM_EMAIL", None) else ""
        pw = getattr(settings, "STREAM_PASSWORD", "") or ""
        auth_part = f"{email}:{pw}@" if email and pw else ""

        catalogue = []
        for cam in cameras:
            cid = cam.camera_id
            catalogue.append({
                "id": cid,
                "name": cam.name,
                "location": cam.location,
                "codec": "h264",
                "live": cam.status == "online",
                "status": cam.status,
                "latitude": cam.latitude,
                "longitude": cam.longitude,
                "urls": {
                    "rtsp": f"rtsp://{auth_part}{stream_host}:8554/stream/{cid.lower()}",
                    "webrtc": f"http://{stream_host}:8889/stream/{cid.lower()}/whep",
                    "hls": f"https://cctv.corp8.cloud/{cid.lower()}/index.m3u8"
                }
            })
        return catalogue
    except Exception as e:
        logger.error(f"Error generating ingest catalogue: {e}")
        return []


# ── In-Memory Camera List Cache with Disk Fallback ──────────────────────────
import json
from pathlib import Path

SNAPSHOT_DIR = Path(__file__).resolve().parent.parent.parent / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
_CAMERAS_JSON_FILE = SNAPSHOT_DIR / "cameras_cache.json"


def _load_cameras_from_disk():
    if _CAMERAS_JSON_FILE.exists():
        try:
            raw = json.loads(_CAMERAS_JSON_FILE.read_text(encoding="utf-8"))
            return [CameraResponse(**item) for item in raw]
        except Exception as e:
            logger.warning(f"Could not load cameras from disk cache: {e}")
    return []


_camera_list_cache = {"data": _load_cameras_from_disk(), "ts": time.time()}
_camera_list_lock = threading.Lock()
_CAMERA_CACHE_TTL = 60.0  # seconds


def _save_cameras_to_disk(cams_data):
    try:
        raw = [c.dict() if hasattr(c, "dict") else c for c in cams_data]
        _CAMERAS_JSON_FILE.write_text(json.dumps(raw, default=str), encoding="utf-8")
    except Exception:
        pass


def invalidate_camera_cache():
    with _camera_list_lock:
        _camera_list_cache["ts"] = 0.0


@router.get("/", response_model=List[CameraResponse])
async def list_cameras(db: Session = Depends(get_db)):
    """
    Get all configured cameras instantly from memory/disk cache with zero DB overhead on cache hits.
    """
    now = time.time()
    with _camera_list_lock:
        if _camera_list_cache["data"] and (now - _camera_list_cache["ts"]) < _CAMERA_CACHE_TTL:
            return _camera_list_cache["data"]

    try:
        cameras = db.query(Camera).order_by(Camera.camera_id).all()
        result = [CameraResponse.from_orm(cam) for cam in cameras]
        if result:
            with _camera_list_lock:
                _camera_list_cache["data"] = result
                _camera_list_cache["ts"] = now
            _save_cameras_to_disk(result)
            return result
    except Exception as e:
        logger.error(f"Error fetching cameras from DB: {e}")

    with _camera_list_lock:
        if _camera_list_cache["data"]:
            return _camera_list_cache["data"]

    # Final fallback to disk
    disk_cams = _load_cameras_from_disk()
    if disk_cams:
        return disk_cams

    return []


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: str,
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

@router.post("/{camera_id}/webrtc")
async def webrtc_offer(camera_id: str, request: Request):
    """Proxy WebRTC WHEP offer to Sentinel MediaMTX with authentication"""
    offer = await request.body()
    
    import httpx
    from app.core.config import settings
    
    stream_email = settings.STREAM_EMAIL
    stream_password = settings.STREAM_PASSWORD
    stream_host = getattr(settings, "STREAM_HOST", "103.250.160.189")
    
    # MediaMTX WHEP endpoint with HTTP Basic Auth
    url = f"http://{stream_host}:8889/stream/{camera_id.lower()}/whep"
    auth = (stream_email, stream_password) if stream_email and stream_password else None
        
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                content=offer,
                headers={"Content-Type": "application/sdp"},
                auth=auth,
                timeout=10.0
            )
        if resp.status_code == 201:
            headers = {"Content-Type": "application/sdp"}
            if "Location" in resp.headers:
                headers["Location"] = resp.headers["Location"]
            return Response(status_code=201, content=resp.text, media_type="application/sdp", headers=headers)
        else:
            logger.warning(f"WebRTC WHEP returned {resp.status_code} for {camera_id}: {resp.text[:200]}")
            return Response(status_code=resp.status_code, content=resp.text)
    except Exception as e:
        logger.error(f"WebRTC proxy error for {camera_id}: {e}")
        return Response(status_code=500, content=str(e))

from app.models.models import RegisteredVehicle, VehicleDetection
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import asyncio
import threading
import numpy as np
import cv2
import time
import os

# ── Snapshot Persistence & Memory Cache ─────────────────────────────────────
SNAPSHOT_DIR = Path(__file__).resolve().parent.parent.parent / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

# In-memory snapshot cache: maps camera_id (lowercase) -> {"jpeg": bytes, "ts": float}
_snapshot_cache: dict = {}
_snapshot_lock = threading.Lock()
_SNAPSHOT_TTL = 300.0  # seconds – memory cache validity

try:
    for _snap_p in SNAPSHOT_DIR.glob("*.jpg"):
        _cid = _snap_p.stem.lower()
        _snapshot_cache[_cid] = {"jpeg": _snap_p.read_bytes(), "ts": time.time()}
except Exception:
    pass


def update_snapshot_cache(camera_id: str, jpeg_bytes: bytes):
    """Save a snapshot to both memory cache and disk"""
    cid = camera_id.lower()
    with _snapshot_lock:
        _snapshot_cache[cid] = {"jpeg": jpeg_bytes, "ts": time.time()}
    try:
        snap_file = SNAPSHOT_DIR / f"{cid}.jpg"
        snap_file.write_bytes(jpeg_bytes)
    except Exception:
        pass


def _sync_capture_rtsp_frame(camera_id: str) -> bytes | None:
    """
    Synchronously connect to RTSP over TCP, grab one frame, and return JPEG bytes.
    Optimized for low-spec CPU: fast timeout, immediate release, downscaled to 640x360.
    """
    from app.core.config import settings
    stream_email = settings.STREAM_EMAIL
    stream_password = settings.STREAM_PASSWORD
    stream_host = getattr(settings, "STREAM_HOST", "103.250.160.189")

    if not (stream_email and stream_password):
        return None

    encoded_email = stream_email.replace("@", "%40")
    rtsp_url = f"rtsp://{encoded_email}:{stream_password}@{stream_host}:8554/stream/{camera_id.lower()}"

    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000"
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        return None

    frame = None
    try:
        valid_frames = 0
        for _ in range(40):  # Grab up to 40 frames to reach a clean keyframe
            ok, f = cap.read()
            if ok and f is not None and f.size > 0:
                valid_frames += 1
                frame = f
                if valid_frames > 15: # Skip the first 15 valid frames to get past decode artifacts
                    break
            time.sleep(0.05)
    finally:
        cap.release()

    if frame is None:
        return None

    # Downscale to 640x360 for fast thumbnail transfer and low memory
    if frame.shape[1] > 640:
        frame = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)

    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return buf.tobytes() if ok else None


@router.get("/{camera_id}/snapshot")
async def get_camera_snapshot(camera_id: str):
    """
    Return camera snapshot instantly from memory cache or disk.
    Zero-blocking architecture.
    """
    cid = camera_id.lower()
    now = time.time()

    # 1. Check in-memory cache
    with _snapshot_lock:
        cached = _snapshot_cache.get(cid)
        if cached and (now - cached["ts"]) < _SNAPSHOT_TTL:
            return Response(content=cached["jpeg"], media_type="image/jpeg", headers={"Cache-Control": "public, max-age=60"})

    # 2. Check disk cache - ALWAYS serve immediately if present!
    snap_file = SNAPSHOT_DIR / f"{cid}.jpg"
    if snap_file.exists():
        try:
            img_data = snap_file.read_bytes()
            if len(img_data) > 500:
                with _snapshot_lock:
                    _snapshot_cache[cid] = {"jpeg": img_data, "ts": now}
                return Response(content=img_data, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=60"})
        except Exception:
            pass

    # 3. Fallback placeholder (instant, non-blocking)
    placeholder = np.zeros((360, 640, 3), dtype=np.uint8)
    cv2.putText(placeholder, f"{camera_id.upper()}",
                (180, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 2)
    _, buf = cv2.imencode(".jpg", placeholder, [cv2.IMWRITE_JPEG_QUALITY, 60])
    return Response(content=buf.tobytes(), media_type="image/jpeg", headers={"Cache-Control": "public, max-age=10"})


@router.get("/{camera_id}/stream")
async def stream_camera(camera_id: str, request: Request, preview: int = 0):
    """
    MJPEG stream with real-time YOLO vehicle detection and license plate overlays.
    Direct RTSP over TCP connection with frame pacing for low-spec CPU.
    """
    async def generate_frames():
        from app.database import SessionLocal
        from app.core.config import settings

        db = SessionLocal()
        cam_db_id = None
        try:
            camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
            if not camera:
                return
            cam_db_id = camera.id
        finally:
            db.close()

        stream_email = settings.STREAM_EMAIL
        stream_password = settings.STREAM_PASSWORD
        stream_host = getattr(settings, "STREAM_HOST", "103.250.160.189")

        if not (stream_email and stream_password):
            return

        cid = camera_id.lower()

        # Instantly yield current snapshot as first frame so modal/card appears without delay
        snap_file = SNAPSHOT_DIR / f"{cid}.jpg"
        if snap_file.exists():
            try:
                init_data = snap_file.read_bytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + init_data + b'\r\n')
            except Exception:
                pass
        else:
            init_frame = np.zeros((360, 640, 3), dtype=np.uint8)
            cv2.putText(init_frame, f"CONNECTING {camera_id.upper()}...",
                        (60, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 200, 255), 2)
            _, init_buf = cv2.imencode('.jpg', init_frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + init_buf.tobytes() + b'\r\n')

        encoded_email = stream_email.replace("@", "%40")
        rtsp_url = f"rtsp://{encoded_email}:{stream_password}@{stream_host}:8554/stream/{cid}"

        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;3000000"
        cap = await asyncio.to_thread(cv2.VideoCapture, rtsp_url, cv2.CAP_FFMPEG)

        if not cap.isOpened():
            logger.error(f"Failed to open RTSP stream for {camera_id}")
            offline = np.zeros((360, 640, 3), dtype=np.uint8)
            cv2.putText(offline, f"{camera_id.upper()} RECONNECTING",
                        (120, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 165, 255), 2)
            _, obuf = cv2.imencode('.jpg', offline, [cv2.IMWRITE_JPEG_QUALITY, 50])
            ob = obuf.tobytes()
            for _ in range(5):
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + ob + b'\r\n')
                await asyncio.sleep(1)
            return

        # Mark online
        if cam_db_id:
            try:
                dbu = SessionLocal()
                c = dbu.query(Camera).filter(Camera.id == cam_db_id).first()
                if c:
                    c.status = "online"
                    c.last_heartbeat = datetime.utcnow()
                    dbu.commit()
                dbu.close()
            except Exception:
                pass

        # AI detection disabled as requested by user to ensure smooth playback
        yolo_detector = None
        ocr = None

        frame_count = 0
        last_detections = []
        consecutive_fails = 0
        # No inference means we can stream faster
        frame_delay = 0.05 if preview else 0.033
        jpeg_quality = 65 if preview else 80

        try:
            while cap.isOpened():
                if await request.is_disconnected():
                    break

                ret, frame = await asyncio.to_thread(cap.read)

                if not ret or frame is None:
                    consecutive_fails += 1
                    if consecutive_fails > 15:
                        logger.warning(f"[{camera_id}] Stream read timeout")
                        break
                    await asyncio.sleep(0.08)
                    continue

                consecutive_fails = 0
                frame_count += 1

                # Downscale to 640x360 to save CPU and bandwidth
                if frame.shape[1] != 640 or frame.shape[0] != 360:
                    frame = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)

                # Periodically update snapshot cache from the active stream
                if frame_count % 30 == 0:
                    try:
                        _, s_buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
                        update_snapshot_cache(camera_id, s_buf.tobytes())
                    except Exception:
                        pass

                # AI Inference (only if detector loaded)
                if yolo_detector and frame_count % INFERENCE_INTERVAL == 0:
                    try:
                        raw_dets = await asyncio.to_thread(yolo_detector.detect_vehicles, frame)
                        last_detections = raw_dets

                        # Save detections to DB (only in modal/full view, to preserve DB throughput)
                        if not preview and last_detections and cam_db_id:
                            db_s = SessionLocal()
                            try:
                                for det in last_detections:
                                    bbox = det["bbox"]
                                    plate_region = await asyncio.to_thread(yolo_detector.detect_plates, frame, bbox)
                                    plate_text, plate_conf = "", 0.0
                                    if plate_region and ocr:
                                        ocr_res = await asyncio.to_thread(ocr.recognize_plate, frame, plate_region["bbox"])
                                        if ocr_res and ocr_res.get("normalized_text") and ocr_res.get("confidence", 0) > 0.85:
                                            plate_text = ocr_res["normalized_text"]
                                            plate_conf = ocr_res["confidence"]
                                    color = await asyncio.to_thread(yolo_detector.detect_color, frame, bbox)
                                    try:
                                        db_s.add(VehicleDetection(
                                            camera_id=cam_db_id,
                                            detected_at=datetime.utcnow(),
                                            vehicle_class=det["class"],
                                            vehicle_confidence=det["confidence"],
                                            plate_number=plate_text or None,
                                            plate_confidence=plate_conf if plate_text else None,
                                            vehicle_color=color
                                        ))
                                        db_s.commit()
                                    except Exception:
                                        db_s.rollback()
                            except Exception as e:
                                logger.error(f"DB save error: {e}")
                            finally:
                                db_s.close()
                    except Exception as e:
                        logger.error(f"Detection error [{camera_id}]: {e}")

                # Draw bounding boxes & labels
                for det in last_detections:
                    x1, y1, x2, y2 = map(int, det['bbox'])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 230, 100), 2)
                    label = f"{det.get('vehicle_color', '')} {det['class']} {det['confidence']:.0%}".strip()
                    cv2.putText(frame, label, (x1, max(y1 - 5, 12)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 230, 100), 1)

                ok, buf = await asyncio.to_thread(cv2.imencode, '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                if ok:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')

                # Frame rate pacing to keep CPU low
                await asyncio.sleep(frame_delay)

        except (GeneratorExit, asyncio.CancelledError):
            pass
        except Exception as e:
            logger.error(f"Stream error [{camera_id}]: {e}")
        finally:
            cap.release()

    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/{camera_id}/ws-stream")
async def websocket_stream_camera(websocket: WebSocket, camera_id: str, preview: int = 0):
    """
    WebSocket MJPEG stream. Bypasses browser HTTP/1.1 connection limits.
    """
    await websocket.accept()
    
    from app.core.config import settings
    stream_email = settings.STREAM_EMAIL
    stream_password = settings.STREAM_PASSWORD
    stream_host = getattr(settings, "STREAM_HOST", "103.250.160.189")

    if not (stream_email and stream_password):
        await websocket.close()
        return

    cid = camera_id.lower()
    encoded_email = stream_email.replace("@", "%40")
    rtsp_url = f"rtsp://{encoded_email}:{stream_password}@{stream_host}:8554/stream/{cid}"

    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;3000000"
    cap = await asyncio.to_thread(cv2.VideoCapture, rtsp_url, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        logger.error(f"Failed to open RTSP stream for {camera_id} via WS")
        offline = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(offline, f"{camera_id.upper()} RECONNECTING",
                    (120, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 165, 255), 2)
        _, obuf = cv2.imencode('.jpg', offline, [cv2.IMWRITE_JPEG_QUALITY, 50])
        ob = obuf.tobytes()
        try:
            for _ in range(5):
                await websocket.send_bytes(ob)
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            pass
        return

    frame_delay = 0.05 if preview else 0.033
    jpeg_quality = 65 if preview else 80
    consecutive_fails = 0

    try:
        while cap.isOpened():
            ret, frame = await asyncio.to_thread(cap.read)

            if not ret or frame is None:
                consecutive_fails += 1
                if consecutive_fails > 15:
                    break
                await asyncio.sleep(0.08)
                continue

            consecutive_fails = 0

            if frame.shape[1] != 640 or frame.shape[0] != 360:
                frame = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)

            ok, buf = await asyncio.to_thread(cv2.imencode, '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
            if ok:
                await websocket.send_bytes(buf.tobytes())

            await asyncio.sleep(frame_delay)
    except WebSocketDisconnect:
        logger.info(f"Client disconnected WS for {camera_id}")
    except Exception as e:
        logger.error(f"WS Stream error [{camera_id}]: {e}")
    finally:
        cap.release()


@router.get("/{camera_id}/live-detections")
async def get_live_detections(camera_id: str, db: Session = Depends(get_db)):
    """Get the latest real-time ML detections from the database"""
    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        return []
    
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
            "plate_number": d.plate_number if d.plate_confidence and d.plate_confidence > 0.80 else None,
            "confidence": round((getattr(d, "vehicle_confidence", None) or 0) * 100, 1),
            "detected_at": d.detected_at.isoformat() + "Z" if d.detected_at else datetime.utcnow().isoformat() + "Z"
        }
        for d in detections
    ]


# ── Background Snapshot Warmer ───────────────────────────────────────────────
def _warmup_camera_snapshots():
    """
    Gently warms up camera snapshots in the background on startup.
    Runs 1 camera every 2.5 seconds to keep CPU usage < 5%.
    """
    time.sleep(3)  # Wait for DB and server startup
    logger.info("Starting background snapshot pre-warming loop...")
    from app.database import SessionLocal
    while True:
        try:
            db = SessionLocal()
            cams = db.query(Camera).filter(Camera.enabled == True).order_by(Camera.camera_id).all()
            cam_ids = [c.camera_id for c in cams]
            db.close()

            for cid in cam_ids:
                # If disk snapshot exists and is less than 3 minutes old, skip to save CPU
                snap_file = SNAPSHOT_DIR / f"{cid.lower()}.jpg"
                if snap_file.exists() and (time.time() - snap_file.stat().st_mtime) < 180.0:
                    continue

                try:
                    jpeg = _sync_capture_rtsp_frame(cid)
                    if jpeg:
                        update_snapshot_cache(cid, jpeg)
                        logger.info(f"[Warmup] Snapshot updated for {cid}")
                except Exception as e:
                    logger.debug(f"[Warmup] Could not refresh {cid}: {e}")

                time.sleep(2.5)  # Gentle spacing between cameras

            time.sleep(60)  # Rest 60s before next cycle
        except Exception as e:
            logger.error(f"[Warmup] Error in warmer loop: {e}")
            time.sleep(30)


# Background warmer enabled to automatically populate camera thumbnails
_warmer_thread = threading.Thread(target=_warmup_camera_snapshots, daemon=True, name="snap_warmer")
_warmer_thread.start()


