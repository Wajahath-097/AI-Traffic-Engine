import cv2
import os
import sys
import glob
import subprocess
from datetime import datetime
import time

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.models import Camera, VehicleDetection
from app.ai.detection import get_yolo_detector, get_ocr_engine

def process_video(video_path, camera_id):
    # If the video is already a processed video, skip it to avoid double processing
    if video_path.endswith("_processed.mp4"):
        print(f"Skipping already processed video: {video_path}")
        return
        
    final_out_path = video_path.replace('.mp4', '_processed.mp4')
    if os.path.exists(final_out_path):
        print(f"Processed video already exists. Skipping: {video_path}")
        return
        
    print(f"Processing video: {video_path} for camera {camera_id}")
    
    # Initialize DB session
    db = SessionLocal()
    
    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        print(f"Camera {camera_id} not found in DB! Skipping.")
        return
        
    yolo = get_yolo_detector()
    ocr = get_ocr_engine()
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video file {video_path}")
        return
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    # Save processed frames to a temporary AVI file
    temp_out_path = video_path.replace('.mp4', '_temp.avi')
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out_writer = cv2.VideoWriter(temp_out_path, fourcc, fps, (width, height))
        
    # Process every frame for smooth output video
    process_every = 1
    frame_count = 0
    seen_plates = set()
    
    last_detections = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        if frame_count % process_every == 0:
            print(f"Processing frame {frame_count}...")
            detections = yolo.detect_vehicles(frame, confidence_threshold=0.25)
            last_detections = []
            
            for det in detections:
                bbox = det['bbox'] # [x1, y1, x2, y2]
                vehicle_class = det['class']
                vehicle_conf = det['confidence']
                
                # Detect color and model
                color = yolo.detect_color(frame, bbox)
                model = yolo.detect_vehicle_model(vehicle_class)
                
                # Detect plate
                plate_bbox = yolo.detect_plates(frame, bbox)
                plate_text = ""
                plate_conf = 0.0
                
                if plate_bbox:
                    ocr_result = ocr.recognize_plate(frame, plate_bbox['bbox'])
                    plate_text = ocr_result.get('normalized_text', '')
                    plate_conf = ocr_result.get('confidence', 0.0)
                    
                    if plate_text:
                        # Normalize first
                        plate_text = ''.join(c for c in plate_text if c.isalnum()).upper()
                        
                        if len(plate_text) >= 4:
                            # Force MH since videos are from Maharashtra
                            if not plate_text.startswith("MH"):
                                if plate_text[:2].isalpha():
                                    plate_text = "MH" + plate_text[2:]
                                else:
                                    plate_text = "MH" + plate_text

                        # If confidence is < 90%, do not show plate
                        if plate_conf < 0.90:
                            plate_text = ""
                            plate_conf = 0.0
                    
                if plate_text:
                    if plate_text in seen_plates:
                        insert_to_db = False
                    else:
                        seen_plates.add(plate_text)
                        insert_to_db = True
                else:
                    insert_to_db = True

                if insert_to_db:
                    v_det = VehicleDetection(
                        camera_id=camera.id,
                        detected_at=datetime.utcnow(),
                        vehicle_class=vehicle_class,
                        vehicle_color=color,
                        vehicle_model=model,
                        vehicle_confidence=vehicle_conf,
                        plate_number=plate_text if plate_text else None,
                        plate_confidence=plate_conf if plate_text else None,
                        ocr_engine="paddleocr" if plate_text else None
                    )
                    db.add(v_det)
                    db.flush()  # To get v_det.id for the alert

                    # Check blacklist
                    from app.models.models import BlacklistEntry, Alert
                    blacklist_match = db.query(BlacklistEntry).filter(BlacklistEntry.plate_number == plate_text).first()
                    if blacklist_match:
                        alert = Alert(
                            severity=blacklist_match.severity or "critical",
                            alert_type="blacklist_match",
                            plate_number=plate_text,
                            camera_id=camera.id,
                            detection_id=v_det.id,
                            message=f"Blacklisted vehicle detected: {plate_text} - {blacklist_match.reason}"
                        )
                        db.add(alert)
                last_detections.append({
                    'bbox': bbox,
                    'class': vehicle_class,
                    'color': color,
                    'model': model,
                    'plate': plate_text,
                    'plate_bbox': plate_bbox['bbox'] if plate_bbox else None
                })
                
            db.commit()
            
        # Draw on frame for visualization
        for det in last_detections:
            x1, y1, x2, y2 = [int(v) for v in det['bbox']]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            if det.get('plate_bbox'):
                px1, py1, px2, py2 = [int(v) for v in det['plate_bbox']]
                cv2.rectangle(frame, (px1, py1), (px2, py2), (0, 0, 255), 2)
            
            # Draw background for text to make it readable — show only: PLATE | TYPE | COLOR
            if det.get('plate'):
                label = f"{det['plate']} | {det['class'].upper()} | {det['color'].upper()}"
            else:
                label = f"{det['class'].upper()} | {det['color'].upper()}"
            
            font_scale = 0.7
            thickness = 2
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            cv2.rectangle(frame, (x1, max(y1 - 28, 0)), (x1 + tw + 4, max(y1 - 4, 0)), (0, 0, 0), -1)
            cv2.putText(frame, label, (x1 + 2, max(y1 - 8, 0)), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 255), thickness)
            
        # Write the processed frame to output video
        out_writer.write(frame)
            
    cap.release()
    out_writer.release()
    db.close()
    
    # Use ffmpeg to convert the temp AVI to an H.264 MP4 file for browser compatibility
    final_out_path = video_path.replace('.mp4', '_processed.mp4')
    print(f"Converting to H.264 format: {final_out_path}")
    try:
        subprocess.run(["ffmpeg", "-y", "-i", temp_out_path, "-vf", "scale=-1:1080", "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", final_out_path], check=True)
        # Clean up temp file
        if os.path.exists(temp_out_path):
            os.remove(temp_out_path)
    except Exception as e:
        print(f"Error during ffmpeg conversion: {e}")
        
    print(f"Finished processing video: {video_path}")

if __name__ == "__main__":
    # Get the project root directory (d:\ai trafic engine)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    video_dir = os.path.join(project_root, "media", "offline_videos")
    
    video_map = {
        "13020032_3840_2160_30fps.mp4": "CAM-001",
        "13105476_3840_2160_30fps.mp4": "CAM-002",
        "14985169_1920_1080_25fps.mp4": "CAM-003"
    }
    
    # Only get raw source videos, not already-processed ones
    all_videos = glob.glob(os.path.join(video_dir, "*.mp4"))
    videos = [v for v in all_videos if not v.endswith("_processed.mp4")]
    
    if not videos:
        print(f"No source .mp4 files found in {video_dir}")
    else:
        for vid in videos:
            filename = os.path.basename(vid)
            cam_id = video_map.get(filename, "CAM-001")
            
            # Skip if already processed (output file exists)
            final_out = vid.replace('.mp4', '_processed.mp4')
            if os.path.exists(final_out):
                print(f"Skipping {filename} — already processed ({final_out})")
                continue
            
            print(f"Processing {filename} for {cam_id}...")
            process_video(vid, cam_id)
    
    print("All video processing complete.")

