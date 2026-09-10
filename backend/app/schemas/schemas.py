"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ==================== Authentication Schemas ====================

class LoginRequest(BaseModel):
    officer_id: str
    password: str
    
    class Config:
        schema_extra = {
            "example": {
                "officer_id": "OFF001",
                "password": "secure_password"
            }
        }


class UserBase(BaseModel):
    officer_id: str
    name: str
    role_id: Optional[UUID] = None


class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==================== Camera Schemas ====================

class CameraBase(BaseModel):
    camera_id: str
    name: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    protocol: str = "rtsp"
    stream_secret_ref: Optional[str] = None
    enabled: bool = True


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    enabled: Optional[bool] = None
    status: Optional[str] = None


class CameraResponse(CameraBase):
    id: UUID
    status: str
    last_heartbeat: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CameraHealthResponse(BaseModel):
    id: UUID
    camera_id: UUID
    status: str
    latency_ms: Optional[int]
    error_code: Optional[str]
    message: Optional[str]
    recorded_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Detection Schemas ====================

class VehicleDetectionBase(BaseModel):
    vehicle_class: Optional[str] = None
    vehicle_color: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_confidence: Optional[float] = None
    plate_number: Optional[str] = None
    plate_confidence: Optional[float] = None
    ocr_raw_text: Optional[str] = None
    ocr_normalized_text: Optional[str] = None


class VehicleDetectionCreate(VehicleDetectionBase):
    camera_id: UUID
    detected_at: datetime
    ocr_engine: str = "paddleocr"
    evidence_ref: Optional[str] = None


class VehicleDetectionResponse(VehicleDetectionBase):
    id: UUID
    camera_id: UUID
    detected_at: datetime
    ocr_engine: Optional[str] = None
    ocr_language: Optional[str] = None
    ocr_recheck_count: Optional[int] = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Search Schemas ====================

class VehicleSearchRequest(BaseModel):
    plate: str = Field(..., min_length=1, max_length=50)
    camera_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, le=1000)


class VehicleSearchResponse(BaseModel):
    plate: str
    results: List[VehicleDetectionResponse]


# ==================== Journey/Trajectory Schemas ====================

class JourneyEventResponse(BaseModel):
    id: UUID
    detection_id: UUID
    sequence_number: int
    detection: Optional[VehicleDetectionResponse] = None
    
    class Config:
        from_attributes = True


class JourneyBase(BaseModel):
    plate_number: str
    start_time: datetime
    end_time: Optional[datetime] = None
    confidence: Optional[float] = None


class JourneyCreate(JourneyBase):
    pass


class JourneyResponse(JourneyBase):
    id: UUID
    start_camera_id: Optional[UUID] = None
    end_camera_id: Optional[UUID] = None
    journey_events: List[JourneyEventResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TrajectoryMapData(BaseModel):
    """GIS-compatible trajectory data"""
    journey_id: UUID
    plate_number: str
    geojson: dict  # GeoJSON FeatureCollection


# ==================== Alert Schemas ====================

class AlertBase(BaseModel):
    severity: str
    alert_type: str
    plate_number: Optional[str] = None
    message: str


class AlertCreate(AlertBase):
    camera_id: Optional[UUID] = None
    detection_id: Optional[UUID] = None
    evidence_ref: Optional[str] = None


class AlertUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[UUID] = None


class AlertResponse(AlertBase):
    id: UUID
    camera_id: Optional[UUID]
    detection_id: Optional[UUID]
    status: str
    assigned_to: Optional[UUID]
    created_at: datetime
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AlertSummary(BaseModel):
    total_alerts: int
    by_severity: dict
    by_status: dict
    by_type: dict


# ==================== Analytics Schemas ====================

class DetectionCountByHour(BaseModel):
    hour: str
    count: int


class CameraStats(BaseModel):
    camera_id: UUID
    camera_name: str
    detection_count: int
    uptime_percentage: float
    last_detection: Optional[datetime]


class DashboardAnalytics(BaseModel):
    total_detections: int
    detections_by_hour: List[DetectionCountByHour]
    top_cameras: List[CameraStats]
    camera_uptime: dict
    alert_summary: AlertSummary


class OCRAccuracyStats(BaseModel):
    average_confidence: float
    high_confidence_count: int
    low_confidence_count: int
    total_recognitions: int
    confidence_distribution: dict


class TrafficPattern(BaseModel):
    camera_id: UUID
    time_slot: str
    average_vehicles: float
    peak_hour: str


# ==================== Blacklist Schemas ====================

class BlacklistEntryCreate(BaseModel):
    plate_number: str
    reason: str
    severity: str
    expires_at: Optional[datetime] = None


class BlacklistEntryResponse(BaseModel):
    id: UUID
    plate_number: str
    reason: str
    severity: str
    created_at: datetime
    expires_at: Optional[datetime]
    vehicle_class: Optional[str] = None
    vehicle_color: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== Audit Log Schemas ====================

class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    action: str
    resource_type: str
    resource_id: str
    details: Optional[dict]
    ip_address: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Error Response ====================

class ErrorResponse(BaseModel):
    detail: str
    error_code: str


# ==================== Role Schemas ====================

class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    
    class Config:
        from_attributes = True
