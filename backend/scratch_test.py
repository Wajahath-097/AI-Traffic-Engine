import cv2
import os

url = "https://cctv.corp8.cloud/cam01/index.m3u8"
print(f"Testing {url}...")
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "stimeout;1000000"
cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
if cap.isOpened():
    print("SUCCESS: HLS")
else:
    print("FAILED: HLS")

url2 = "rtsp://mdwajahathullahshareef%40gmail.com:LFQP-568P-M28D@103.250.160.189:8554/stream/cam01"
print(f"Testing {url2}...")
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;1000000"
cap = cv2.VideoCapture(url2, cv2.CAP_FFMPEG)
if cap.isOpened():
    print("SUCCESS: RTSP")
else:
    print("FAILED: RTSP")
