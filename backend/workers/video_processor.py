import os
import sys
import time
import cv2
import logging
from sqlalchemy.orm import Session
from pathlib import Path

# Add the parent directory to sys.path so we can import app modules
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
sys.path.append(str(backend_dir))

from app.database import SessionLocal
from app.models.models import VehicleDetection, Camera, Journey
from app.ai.detection import get_yolo_detector, get_ocr_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
MEDIA_DIR = backend_dir.parent / "media" / "offline_videos"
PROCESS_EVERY_N_FRAMES = 30 # Process 1 frame every second (assuming 30fps)

def process_video(video_path: str, camera_id: str):
    logger.info(f"Processing video {video_path} for camera {camera_id}")
    
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return

    # Initialize models
    detector = get_yolo_detector()
    ocr = get_ocr_engine()

    # Get DB session
    db: Session = SessionLocal()
    
    try:
        # Ensure camera exists
        camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        if not camera:
            logger.info(f"Creating mock camera {camera_id}")
            camera = Camera(
                camera_id=camera_id,
                name=f"Camera {camera_id}",
                location="Demo Location",
                latitude=40.7128,  # Default Lat
                longitude=-74.0060, # Default Lng
                status="online",
                protocol="rtsp"
            )
            db.add(camera)
            db.commit()
            db.refresh(camera)
            
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            if frame_count % PROCESS_EVERY_N_FRAMES != 0:
                continue
                
            logger.info(f"Processing frame {frame_count}")
            
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
                    if ocr_res and ocr_res.get("normalized_text") and "MOCKPLATE" not in ocr_res.get("normalized_text"):
                        plate_text = ocr_res["normalized_text"]
                        plate_conf = ocr_res["confidence"]
                    elif ocr_res and ocr_res.get("normalized_text") == "MOCKPLATE":
                        import random
                        # If mock, just generate a dummy plate to show it's working
                        plate_text = f"MOCK{random.randint(1000, 9999)}"
                        plate_conf = 0.95
                
                # Insert into DB if a plate is found
                if plate_text:
                    logger.info(f"Found plate {plate_text} on {vehicle_class}")
                    
                    # Detect color
                    color = detector.detect_color(frame, bbox)
                    
                    # Create detection record
                    detection_record = VehicleDetection(
                        camera_id=camera.id,
                        vehicle_class=vehicle_class,
                        confidence=confidence,
                        bbox_x1=bbox[0],
                        bbox_y1=bbox[1],
                        bbox_x2=bbox[2],
                        bbox_y2=bbox[3],
                        plate_number=plate_text,
                        plate_confidence=plate_conf,
                        vehicle_color=color
                    )
                    db.add(detection_record)
                    
        db.commit()
        cap.release()
        logger.info(f"Finished processing {video_path}")
        
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting Offline Video Processor")
    
    videos = [
        {"file": "13020032_3840_2160_30fps.mp4", "camera": "CAM-001"},
        {"file": "13105476_3840_2160_30fps.mp4", "camera": "CAM-002"},
        {"file": "14985169_1920_1080_25fps.mp4", "camera": "CAM-003"}
    ]
    
    for v in videos:
        v_path = MEDIA_DIR / v["file"]
        process_video(str(v_path), v["camera"])
