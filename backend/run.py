#!/usr/bin/env python
"""
Entry point for running the Traffic AI Engine backend
"""

import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000"

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=settings.FASTAPI_ENV == "development",
        workers=1 if settings.FASTAPI_ENV == "development" else settings.FASTAPI_WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )
