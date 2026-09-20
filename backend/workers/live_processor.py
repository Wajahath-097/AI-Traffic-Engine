"""
Multi-camera live AI processor for vehicle detection.

Connects to the Sentinel Camera Grid via HLS (primary) or RTSP (fallback)
and runs YOLOv8-nano inference on frames to detect vehicles, their types,
colours, and licence plates.

Optimised for Intel Pentium Silver / no-GPU:
  • yolov8n (nano) model
  • Inference on 640×360 downscaled frames
  • Process one frame every 5 seconds per camera
  • Max 2 concurrent camera threads (Pentium safe)
"""

import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000"
import sys
import time
import cv2
import logging
import datetime
from pathlib import Path
import threading

# Add the parent directory to sys.path so we can import app modules
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
sys.path.append(str(backend_dir))

from app.database import SessionLocal
from app.models.models import VehicleDetection, Camera
from app.ai.detection import get_yolo_detector, get_ocr_engine
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────
PROCESS_INTERVAL_SECONDS = 5.0  # Wait between inference frames (CPU-friendly)
MAX_CONCURRENT_CAMERAS = 2      # Pentium Silver can handle ~2 threads with YOLO
RECONNECT_BACKOFF_BASE = 2      # seconds
RECONNECT_BACKOFF_CAP = 30      # seconds


def build_video_url(camera_id: str) -> tuple[str, str | None]:
    """
    Build HLS (primary) and RTSP (fallback) URLs for a camera.
    Returns (hls_url, rtsp_url_or_None).
    """
    hls_url = f"https://cctv.corp8.cloud/{camera_id.lower()}/index.m3u8"

    stream_email = settings.STREAM_EMAIL
    stream_password = settings.STREAM_PASSWORD
    stream_host = getattr(settings, "STREAM_HOST", "103.250.160.189")

    if stream_email and stream_password:
        encoded_email = stream_email.replace("@", "%40")
        rtsp_url = f"rtsp://{encoded_email}:{stream_password}@{stream_host}:8554/stream/{camera_id.lower()}"
    else:
        rtsp_url = None

    return hls_url, rtsp_url


def open_capture(hls_url: str, rtsp_url: str | None) -> cv2.VideoCapture | None:
    """Try HLS first, then RTSP over TCP. Returns an opened VideoCapture or None."""
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "stimeout;5000000"
    cap = cv2.VideoCapture(hls_url, cv2.CAP_FFMPEG)
    if cap.isOpened():
        return cap

    if rtsp_url:
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000"
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        if cap.isOpened():
            return cap

    return None


def process_live_stream(camera_id: str, camera_db_id: str):
    """
    Main loop for one camera. Opens the stream, grabs frames, runs YOLO+OCR,
    and writes detections to the database. Reconnects with exponential backoff.
    """
    logger.info(f"[{camera_id}] Starting live AI processor")

    detector = get_yolo_detector()  # yolov8n singleton
    ocr = get_ocr_engine()

    hls_url, rtsp_url = build_video_url(camera_id)
    retry_count = 0

    while True:
        cap = open_capture(hls_url, rtsp_url)

        if cap is None:
            retry_count += 1
            backoff = min(RECONNECT_BACKOFF_BASE ** retry_count, RECONNECT_BACKOFF_CAP)
            logger.warning(f"[{camera_id}] Cannot open stream, retrying in {backoff}s...")
            time.sleep(backoff)
            continue

        retry_count = 0
        logger.info(f"[{camera_id}] Stream connected")

        # Update DB status
        db = SessionLocal()
        try:
            cam = db.query(Camera).filter(Camera.camera_id == camera_id).first()
            if cam:
                cam.status = "online"
                cam.last_heartbeat = datetime.datetime.utcnow()
                db.commit()
        except Exception:
            pass
        finally:
            db.close()

        consecutive_fails = 0

        try:
            while True:
                ret, frame = cap.read()

                if not ret:
                    consecutive_fails += 1
                    if consecutive_fails > 300:  # ~30 s of silence
                        logger.warning(f"[{camera_id}] Too many failed reads, reconnecting...")
                        break
                    time.sleep(0.1)
                    continue

                consecutive_fails = 0

                # ── Downscale for inference (Pentium-friendly) ───────────
                inf_frame = cv2.resize(frame, (640, 360))

                logger.info(f"[{camera_id}] Running inference...")
                detections = detector.detect_vehicles(inf_frame)

                # Scale bboxes back to original resolution for colour/plate extraction
                sx = frame.shape[1] / 640
                sy = frame.shape[0] / 360

                db = SessionLocal()
                try:
                    for det in detections:
                        bbox_orig = [
                            det["bbox"][0] * sx, det["bbox"][1] * sy,
                            det["bbox"][2] * sx, det["bbox"][3] * sy
                        ]
                        vehicle_class = det["class"]
                        confidence = det["confidence"]

                        # Plate detection + OCR
                        plate_region = detector.detect_plates(frame, bbox_orig)
                        plate_text, plate_conf = "", 0.0
                        if plate_region and ocr:
                            ocr_res = ocr.recognize_plate(frame, plate_region["bbox"])
                            if ocr_res and ocr_res.get("normalized_text") and ocr_res.get("confidence", 0) > 0.85:
                                plate_text = ocr_res["normalized_text"]
                                plate_conf = ocr_res["confidence"]

                        color = detector.detect_color(frame, bbox_orig)
                        logger.info(f"[{camera_id}] {color} {vehicle_class} (conf={confidence:.2f}). Plate: {plate_text or 'None'}")

                        detection_record = VehicleDetection(
                            camera_id=camera_db_id,
                            detected_at=datetime.datetime.utcnow(),
                            vehicle_class=vehicle_class,
                            vehicle_confidence=confidence,
                            plate_number=plate_text if plate_text else None,
                            plate_confidence=plate_conf if plate_text else None,
                            vehicle_color=color
                        )
                        db.add(detection_record)

                    db.commit()
                except Exception as e:
                    logger.error(f"[{camera_id}] DB error: {e}")
                    db.rollback()
                finally:
                    db.close()

                # Wait before next frame to save CPU
                time.sleep(PROCESS_INTERVAL_SECONDS)

        except Exception as e:
            logger.error(f"[{camera_id}] Processor error: {e}")
        finally:
            cap.release()

        # Brief pause before reconnecting
        time.sleep(RECONNECT_BACKOFF_BASE)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("  SENTINEL LIVE AI ENGINE")
    logger.info(f"  Max concurrent cameras: {MAX_CONCURRENT_CAMERAS}")
    logger.info(f"  Inference interval: {PROCESS_INTERVAL_SECONDS}s")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        cameras = db.query(Camera).filter(Camera.enabled == True).limit(MAX_CONCURRENT_CAMERAS).all()
        if not cameras:
            logger.error("No active cameras found in database.")
            sys.exit(1)

        logger.info(f"Processing cameras: {[c.camera_id for c in cameras]}")

        threads = []
        for cam in cameras:
            t = threading.Thread(
                target=process_live_stream,
                args=(cam.camera_id, str(cam.id)),
                daemon=True
            )
            t.start()
            threads.append(t)
            time.sleep(1)  # Stagger thread starts

        # Keep main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down workers...")
    finally:
        db.close()
