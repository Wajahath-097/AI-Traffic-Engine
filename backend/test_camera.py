import cv2
import os

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000"

url1 = "rtsp://mdwajahathullahshareef%40gmail.com:LFQP-568P-M28D@103.250.160.189:8554/stream/CAM01"
url2 = "rtsp://mdwajahathullahshareef%40gmail.com:LFQP-568P-M28D@103.250.160.189:8554/CAM01"
url3 = "https://cctv.corp8.cloud/CAM01/index.m3u8"

for url in [url1, url2, url3]:
    print(f"Testing {url}...")
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    if cap.isOpened():
        print(f"SUCCESS: {url}")
        cap.release()
    else:
        print(f"FAILED: {url}")
