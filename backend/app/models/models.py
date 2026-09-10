"""
SQLAlchemy models for Traffic AI Engine
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum, JSON, UUID, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class Role(Base):
    """User role definition"""
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="role")
    
    def __repr__(self):
        return f"<Role {self.name}>"


class User(Base):
    """User account"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    officer_id = Column(String(50), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    name = Column(String(100), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    role = relationship("Role", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")
    alerts_assigned = relationship("Alert", back_populates="assigned_to_user")
    blacklist_entries_created = relationship("BlacklistEntry", back_populates="created_by_user")
    
    def __repr__(self):
        return f"<User {self.officer_id}>"


class Camera(Base):
    """Camera configuration and status"""
    __tablename__ = "cameras"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    location = Column(String(200))
    latitude = Column(Float)
    longitude = Column(Float)
    protocol = Column(String(20), default="rtsp")
    stream_secret_ref = Column(Text)
    enabled = Column(Boolean, default=True)
    status = Column(String(20), default="unknown")  # online, offline, degraded
    last_heartbeat = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    detections = relationship("VehicleDetection", back_populates="camera")
    health_events = relationship("CameraHealthEvent", back_populates="camera", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="camera")
    journeys_start = relationship("Journey", foreign_keys="Journey.start_camera_id", back_populates="start_camera")
    journeys_end = relationship("Journey", foreign_keys="Journey.end_camera_id", back_populates="end_camera")
    
    def __repr__(self):
        return f"<Camera {self.camera_id}>"


class CameraHealthEvent(Base):
    """Camera stream health monitoring"""
    __tablename__ = "camera_health_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20))  # online, offline, degraded
    latency_ms = Column(Integer)
    error_code = Column(String(50))
    message = Column(Text)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    camera = relationship("Camera", back_populates="health_events")
    
    def __repr__(self):
        return f"<HealthEvent {self.camera_id} {self.status}>"


class VehicleDetection(Base):
    """Vehicle detection from camera feed"""
    __tablename__ = "vehicle_detections"
    __table_args__ = (UniqueConstraint('plate_number', name='uq_vehicle_detection_plate'),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    detected_at = Column(DateTime, nullable=False)
    vehicle_class = Column(Enum('car', 'bus', 'auto', 'bike', 'other', name='vehicle_class_enum'), nullable=True)
    vehicle_color = Column(String(50))  # white, black, red, silver, etc.
    vehicle_model = Column(String(100)) # e.g. Honda Civic, Toyota Corolla
    vehicle_confidence = Column(Float)
    plate_number = Column(String(50))
    plate_confidence = Column(Float)
    ocr_raw_text = Column(Text)
    ocr_normalized_text = Column(Text)
    ocr_engine = Column(String(50))  # paddleocr, tesseract, etc.
    ocr_language = Column(String(10), default="en")
    ocr_recheck_count = Column(Integer, default=0)
    evidence_ref = Column(Text)  # S3 key or local path
    created_at = Column(DateTime, default=datetime.utcnow)
    
    camera = relationship("Camera", back_populates="detections")
    journey_events = relationship("JourneyEvent", back_populates="detection")
    alerts = relationship("Alert", back_populates="detection")
    
    def __repr__(self):
        return f"<Detection {self.camera_id} {self.plate_number}>"


class Journey(Base):
    """Vehicle journey/trajectory across cameras"""
    __tablename__ = "journeys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plate_number = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    confidence = Column(Float)  # Average confidence of detections
    start_camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id"))
    end_camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    start_camera = relationship("Camera", foreign_keys=[start_camera_id], back_populates="journeys_start")
    end_camera = relationship("Camera", foreign_keys=[end_camera_id], back_populates="journeys_end")
    journey_events = relationship("JourneyEvent", back_populates="journey", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Journey {self.plate_number}>"


class JourneyEvent(Base):
    """Detection within a journey"""
    __tablename__ = "journey_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journey_id = Column(UUID(as_uuid=True), ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False)
    detection_id = Column(UUID(as_uuid=True), ForeignKey("vehicle_detections.id", ondelete="CASCADE"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    journey = relationship("Journey", back_populates="journey_events")
    detection = relationship("VehicleDetection", back_populates="journey_events")
    
    def __repr__(self):
        return f"<JourneyEvent {self.journey_id} seq:{self.sequence_number}>"


class Alert(Base):
    """Alert/incident notification"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    severity = Column(String(20))  # critical, high, medium, low
    alert_type = Column(String(50))  # blacklist_match, repeated_hits, low_confidence, offline, anomaly
    plate_number = Column(String(50))
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id"))
    detection_id = Column(UUID(as_uuid=True), ForeignKey("vehicle_detections.id"))
    message = Column(Text)
    evidence_ref = Column(Text)
    status = Column(String(20), default="open")  # open, investigating, resolved, dismissed
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    camera = relationship("Camera", back_populates="alerts")
    detection = relationship("VehicleDetection", back_populates="alerts")
    assigned_to_user = relationship("User", back_populates="alerts_assigned")
    
    def __repr__(self):
        return f"<Alert {self.alert_type} {self.severity}>"


class BlacklistEntry(Base):
    """Blacklisted vehicle registrations"""
    __tablename__ = "blacklist_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plate_number = Column(String(50), unique=True, nullable=False)
    reason = Column(Text)
    severity = Column(String(20))  # critical, high, medium
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)
    
    created_by_user = relationship("User", back_populates="blacklist_entries_created")
    
    def __repr__(self):
        return f"<Blacklist {self.plate_number}>"


class AuditLog(Base):
    """Audit trail for sensitive operations"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)  # login, search, view_trajectory, etc.
    resource_type = Column(String(50))  # user, camera, vehicle, detection, etc.
    resource_id = Column(String(255))
    details = Column(JSON)  # Additional context
    ip_address = Column(String(50))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_id}>"

class RegisteredVehicle(Base):
    """Simulated official RTO/Vahan database"""
    __tablename__ = "registered_vehicles"
    
    plate_number = Column(String(50), primary_key=True)
    vehicle_class = Column(String(50))
    vehicle_color = Column(String(50))
    owner_name = Column(String(100))
    registration_status = Column(String(20), default="Active")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<RTO Vehicle {self.plate_number}>"

