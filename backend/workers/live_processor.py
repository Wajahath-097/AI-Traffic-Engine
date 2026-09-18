import os
import sys
import time
import cv2
import logging
import datetime
from sqlalchemy.orm import Session
from pathlib import Path
import threading

# Add the parent directory to sys.path so we can import app modules
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
sys.path.append(str(backend_dir))

from app.database import SessionLocal
from app.models.models import VehicleDetection, Camera
from app.ai.detection import get_yolo_detector, get_ocr_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
RTSP_BASE_URL = "rtsp://mdwajahathullahshareef%40gmail.com:C3G7-RAPP-2L84@103.250.160.189:8554/stream"
PROCESS_INTERVAL_SECONDS = 5.0 # Wait 5 seconds between processing frames for a given camera to avoid CPU overload
MAX_CONCURRENT_CAMERAS = 2 # Don't melt the PC

def process_live_stream(camera_id: str, camera_db_id: str):
    logger.info(f"Starting live AI processor for camera {camera_id}")
    rtsp_url = f"{RTSP_BASE_URL}/{camera_id}"
    
    detector = get_yolo_detector()
    ocr = get_ocr_engine()
    db = SessionLocal()
    
    cap = cv2.VideoCapture(rtsp_url)
    
    try:
        while True:
            # Capture frame
            ret, frame = cap.read()
            if not ret:
                logger.warning(f"Failed to read from stream {camera_id}, attempting reconnect...")
                cap.release()
                time.sleep(2)
                cap = cv2.VideoCapture(rtsp_url)
                continue
            
            logger.info(f"[{camera_id}] Captured live frame, running inference...")
            
            # Detect vehicles
            detections = detector.detect_vehicles(frame)
            
            for det in detections:
                bbox = det["bbox"]
                vehicle_class = det["class"]
                confidence = det["confidence"]
                
                # Detect plate
                plate_region = detector.detect_plates(frame, bbox)
                plate_text = ""
                plate_conf = 0.0
                
                if plate_region:
                    ocr_res = ocr.recognize_plate(frame, plate_region["bbox"])
                    if ocr_res and ocr_res.get("normalized_text") and ocr_res.get("confidence", 0) > 0.85:
                        plate_text = ocr_res["normalized_text"]
                        plate_conf = ocr_res["confidence"]
                
                # Insert into DB
                color = detector.detect_color(frame, bbox)
                logger.info(f"[{camera_id}] Found {color} {vehicle_class}. Plate: {plate_text or 'None'}")
                
                try:
                    detection_record = VehicleDetection(
                        camera_id=camera_db_id,
                        detected_at=datetime.datetime.utcnow(),
                        vehicle_class=vehicle_class,
                        confidence=confidence,
                        plate_number=plate_text if plate_text else None,
                        plate_confidence=plate_conf if plate_text else None,
                        vehicle_color=color
                    )
                    db.add(detection_record)
                    db.commit()
                except Exception as e:
                    logger.error(f"[{camera_id}] Failed to save detection: {e}")
                    db.rollback()
            
            # Wait before next frame to save CPU
            time.sleep(PROCESS_INTERVAL_SECONDS)
            
    except Exception as e:
        logger.error(f"Error in processor for {camera_id}: {e}")
    finally:
        cap.release()
        db.close()

if __name__ == "__main__":
    logger.info("Starting Multi-Camera Live AI Engine")
    
    db = SessionLocal()
    try:
        cameras = db.query(Camera).filter(Camera.enabled == True).limit(MAX_CONCURRENT_CAMERAS).all()
        if not cameras:
            logger.error("No active cameras found in database.")
            sys.exit(1)
            
        threads = []
        for cam in cameras:
            t = threading.Thread(target=process_live_stream, args=(cam.camera_id, str(cam.id)))
            t.daemon = True
            t.start()
            threads.append(t)
            
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down workers...")
    finally:
        db.close()
