import os
import sys
import urllib.request
import time
import cv2

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.config import settings

cams = ['cam09', 'cam11', 'cam16', 'cam25', 'cam29']
email = settings.STREAM_EMAIL.replace('@', '%40')
pw = settings.STREAM_PASSWORD
host = getattr(settings, 'STREAM_HOST', '103.250.160.189')

print("Starting camera checks...", flush=True)

for c in cams:
    hls_url = f"https://cctv.corp8.cloud/{c}/index.m3u8"
    rtsp_url = f"rtsp://{email}:{pw}@{host}:8554/stream/{c}"
    
    # Check HLS
    hls_status = "ERR"
    try:
        req = urllib.request.Request(hls_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            hls_status = str(resp.getcode())
    except urllib.error.HTTPError as e:
        hls_status = f"HTTP {e.code}"
    except Exception as e:
        hls_status = f"Exception: {type(e).__name__}"

    # Check RTSP
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;2000000"
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    rtsp_opened = cap.isOpened()
    frame_read = False
    if rtsp_opened:
        ret, frame = cap.read()
        frame_read = ret and frame is not None
        cap.release()

    print(f"[{c.upper()}] HLS: {hls_status} | RTSP Opened: {rtsp_opened} | Frame Read: {frame_read}", flush=True)

print("Check finished!", flush=True)
