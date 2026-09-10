-- Initial Traffic AI Engine Schema
-- Database: traffic_ai
-- Author: Mind Mesh
-- Date: 2026-09-01

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    officer_id VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name VARCHAR(100) NOT NULL,
    role_id UUID,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Roles table
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add role FK constraint
ALTER TABLE users ADD CONSTRAINT fk_user_role FOREIGN KEY (role_id) REFERENCES roles(id);

-- Cameras table
CREATE TABLE cameras (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    protocol VARCHAR(20),
    stream_secret_ref TEXT,
    enabled BOOLEAN DEFAULT true,
    status VARCHAR(20) DEFAULT 'unknown',
    last_heartbeat TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location_geom GEOMETRY(Point, 4326)
);

-- Create spatial index
CREATE INDEX idx_cameras_location ON cameras USING GIST(location_geom);

-- Camera health events table
CREATE TABLE camera_health_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_id UUID NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    status VARCHAR(20),
    latency_ms INTEGER,
    error_code VARCHAR(50),
    message TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_camera_health_camera_id ON camera_health_events(camera_id);
CREATE INDEX idx_camera_health_recorded_at ON camera_health_events(recorded_at);

-- Vehicle detections table
CREATE TABLE vehicle_detections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_id UUID NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    detected_at TIMESTAMP NOT NULL,
    vehicle_class VARCHAR(50),
    vehicle_confidence REAL,
    plate_number VARCHAR(50),
    plate_confidence REAL,
    ocr_raw_text TEXT,
    ocr_normalized_text TEXT,
    ocr_engine VARCHAR(50),
    ocr_language VARCHAR(10),
    ocr_recheck_count INTEGER DEFAULT 0,
    evidence_ref TEXT,
    location_geom GEOMETRY(Point, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for detections
CREATE INDEX idx_detections_camera_id ON vehicle_detections(camera_id);
CREATE INDEX idx_detections_plate_number ON vehicle_detections(plate_number);
CREATE INDEX idx_detections_detected_at ON vehicle_detections(detected_at);
CREATE INDEX idx_detections_created_at ON vehicle_detections(created_at);
CREATE INDEX idx_detections_camera_detected ON vehicle_detections(camera_id, detected_at);
CREATE INDEX idx_detections_plate_detected ON vehicle_detections(plate_number, detected_at);
CREATE INDEX idx_detections_location ON vehicle_detections USING GIST(location_geom);

-- Journeys (trajectories)
CREATE TABLE journeys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plate_number VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    confidence REAL,
    start_camera_id UUID REFERENCES cameras(id),
    end_camera_id UUID REFERENCES cameras(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_journeys_plate_number ON journeys(plate_number);
CREATE INDEX idx_journeys_start_time ON journeys(start_time);
CREATE INDEX idx_journeys_created_at ON journeys(created_at);

-- Journey events (detections within a journey)
CREATE TABLE journey_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    journey_id UUID NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    detection_id UUID NOT NULL REFERENCES vehicle_detections(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_journey_events_journey_id ON journey_events(journey_id);
CREATE INDEX idx_journey_events_detection_id ON journey_events(detection_id);

-- Alerts table
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    severity VARCHAR(20),
    alert_type VARCHAR(50),
    plate_number VARCHAR(50),
    camera_id UUID REFERENCES cameras(id),
    detection_id UUID REFERENCES vehicle_detections(id),
    message TEXT,
    evidence_ref TEXT,
    status VARCHAR(20) DEFAULT 'open',
    assigned_to UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
CREATE INDEX idx_alerts_camera_id ON alerts(camera_id);
CREATE INDEX idx_alerts_plate_number ON alerts(plate_number);

-- Blacklist entries
CREATE TABLE blacklist_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plate_number VARCHAR(50) UNIQUE NOT NULL,
    reason TEXT,
    severity VARCHAR(20),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_blacklist_plate_number ON blacklist_entries(plate_number);

-- Audit log
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- Insert default roles
INSERT INTO roles (name, description) VALUES
('officer', 'Traffic Officer - Can view and search'),
('analyst', 'Data Analyst - Can analyze and view'),
('administrator', 'System Administrator - Full access');

-- Create indexes for frequently searched columns
CREATE INDEX idx_users_officer_id ON users(officer_id);
CREATE INDEX idx_users_is_active ON users(is_active);
