import cv2
import os

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;1000000"

host = "103.250.160.189"
email = "mdwajahathullahshareef%40gmail.com"
pw = "LFQP-568P-M28D"

for i in range(1, 35):
    cam_id = f"camera_{i}"
    url = f"rtsp://{email}:{pw}@{host}:8554/{cam_id}"
    print(f"Testing {url}...")
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    if cap.isOpened():
        print(f"SUCCESS: {url}")
        cap.release()
    
    url = f"rtsp://{email}:{pw}@{host}:8554/stream/{cam_id}"
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    if cap.isOpened():
        print(f"SUCCESS: {url}")
        cap.release()
