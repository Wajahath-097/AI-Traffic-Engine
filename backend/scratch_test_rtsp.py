import cv2
import os

url2 = "rtsp://mdwajahathullahshareef%40gmail.com:LFQP-568P-M28D@103.250.160.189:8554/stream/cam01"
print(f"Testing {url2}...")
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;2000000"
cap = cv2.VideoCapture(url2, cv2.CAP_FFMPEG)
if cap.isOpened():
    print("SUCCESS: RTSP")
else:
    print("FAILED: RTSP")
