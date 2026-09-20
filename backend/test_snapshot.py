import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

camera_id = "CAM01"
print(f"Testing snapshot for {camera_id}")

from app.database import SessionLocal
from app.models.models import Camera
db = SessionLocal()
try:
    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        print("Camera not found")
finally:
    db.close()
    
import os
from app.core.config import settings
stream_email = settings.STREAM_EMAIL
stream_password = settings.STREAM_PASSWORD

if stream_email and stream_password:
    encoded_email = stream_email.replace("@", "%40")
    stream_host = getattr(settings, "STREAM_HOST", "103.250.160.189")
    video_path = f"rtsp://{encoded_email}:{stream_password}@{stream_host}:8554/stream/{camera_id.lower()}"
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;1500000"
else:
    video_path = f"https://cctv.corp8.cloud/{camera_id.lower()}/index.m3u8"
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "stimeout;1500000"
    
import cv2
cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
if not cap.isOpened():
    print("Stream offline")
    sys.exit(1)
    
ret = False
frame = None
for _ in range(5):
    ret, frame = cap.read()
    if ret:
        break
    import time
    time.sleep(0.1)
    
cap.release()

if not ret or frame is None:
    print("No frame available")
    sys.exit(1)
    
ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
if not ret:
    print("Could not encode frame")
    sys.exit(1)
    
print("Success!")
