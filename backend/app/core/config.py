"""
Configuration settings for Traffic AI Engine
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # FastAPI settings
    FASTAPI_ENV: str = "development"
    FASTAPI_DEBUG: bool = True
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000
    FASTAPI_WORKERS: int = 4
    
    # Database
    DATABASE_URL: str = "postgresql://traffic_user:traffic_pass@localhost:5432/traffic_ai"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    PASSWORD_MIN_LENGTH: int = 8
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:3000", "http://127.0.0.1:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Kafka
    KAFKA_BROKER_URL: str = "localhost:9092"
    KAFKA_TOPIC_PREFIX: str = "traffic"
    
    # Camera Configuration
    CAMERA_CONFIG_PATH: str = "/app/config/cameras.json"
    MAX_CAMERAS: int = 10
    FRAME_SAMPLE_RATE: int = 5
    INFERENCE_FPS: int = 5
    
    # AI Models
    YOLO_MODEL: str = "yolov8m"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.5
    OCR_ENGINE: str = "paddleocr"
    OCR_LANGUAGE: str = "en"
    OCR_CONFIDENCE_THRESHOLD: float = 0.3
    OCR_RECHECK_THRESHOLD: float = 0.5
    
    # Media Gateway
    MEDIA_GATEWAY_URL: str = "http://localhost:8554"
    MEDIA_GATEWAY_PORT: int = 8554
    RTSP_TIMEOUT_SECONDS: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Storage
    EVIDENCE_STORAGE_PATH: str = "/data/evidence"
    TEMP_FRAME_PATH: str = "/tmp/frames"
    
    # Streaming Credentials
    STREAM_EMAIL: str = ""
    STREAM_PASSWORD: str = ""
    STREAM_HOST: str = "103.250.160.189"
    
    # Data retention
    AUDIT_LOG_RETENTION_DAYS: int = 90
    DATA_RETENTION_DAYS: int = 365
    ENABLE_AUDIT_LOGGING: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
