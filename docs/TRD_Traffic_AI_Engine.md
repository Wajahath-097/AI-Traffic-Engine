# Technical Requirements Document (TRD)
## Traffic AI Engine — City-Wide Multi-Camera ANPR, Trajectory Tracking & Urban Traffic Analytics

**Team:** Mind Mesh  
**SIH Problem Statement ID:** 26127  
**Version:** 1.0  
**Date:** 1 September 2026  
**Status:** Engineering baseline

---

## 1. Purpose

This document defines the technical architecture, components, interfaces, data model, deployment model, non-functional requirements and implementation plan for Traffic AI Engine.

The technical design follows the technology stack stated in the SIH proposal:
- OpenCV
- YOLOv8
- PaddleOCR
- Python
- FastAPI
- Apache Kafka
- PostgreSQL
- React
- Leaflet
- SUMO

The design is intentionally modular so the current ten-camera prototype can evolve into a larger deployment.

---

## 2. High-Level Architecture

```text
                       ┌─────────────────────┐
                       │   Chrome / Browser  │
                       └──────────┬──────────┘
                                  │ HTTPS
                         REST + WebSocket
                                  │
                    ┌─────────────▼─────────────┐
                    │      React Frontend       │
                    │ Dashboard / Cameras / GIS │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │       FastAPI API         │
                    │ Auth / Search / Alerts    │
                    │ Cameras / Analytics       │
                    └───────┬────────┬──────────┘
                            │        │
                    ┌───────▼───┐ ┌──▼───────────┐
                    │ PostgreSQL│ │ Event/WebSock │
                    │ + PostGIS │ │ Notifications │
                    └───────────┘ └──────┬────────┘
                                         │
              ┌──────────────────────────▼─────────────────────┐
              │              AI / Event Pipeline               │
              │                                                │
RTSP ──► Media Gateway ──► Frame Worker ─► YOLO ─► Plate ─► OCR│
              │                                  │             │
              │                                  └──► Events ──┤
              └────────────────────────────────────────────────┘
                                         │
                                  Trajectory Engine
                                         │
                                    GIS / Alerts

Optional scale-out:
Camera Workers → Kafka → AI Consumers → PostgreSQL
```

---

## 3. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| UI icons | Lucide React |
| Routing | React Router |
| GIS | Leaflet + React Leaflet |
| Backend | Python + FastAPI |
| API server | Uvicorn |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Spatial extension | PostGIS |
| Event bus | Apache Kafka |
| Video processing | OpenCV / FFmpeg |
| Stream gateway | MediaMTX or equivalent |
| Detection | YOLOv8 / current supported Ultralytics model |
| OCR | PaddleOCR |
| Simulation | SUMO |
| Auth | JWT or secure server-side session |
| Reverse proxy | Nginx or equivalent |
| Packaging | Native Python venv + Node.js (Vite) |
| Source control | Git |

---

## 4. Repository Structure

Recommended structure:

```text
traffic-ai-engine/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── context/
│   │   ├── assets/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── ai/
│   │   ├── tracking/
│   │   ├── alerts/
│   │   └── core/
│   ├── workers/
│   │   ├── live_processor.py
│   │   └── video_processor.py
│   ├── scripts/
│   ├── snapshots/
│   ├── traffic_ai.db
│   ├── requirements.txt
│   └── run.py
│
├── media/
│   └── mediamtx/
│
├── database/
│   └── migrations/
│
├── docs/
├── .env.example
├── test_api.py
└── README.md
```

---

## 5. Network Architecture

### Browser
Production:
```text
HTTPS 443
```

### Reverse proxy
```text
443 → frontend
443/api → FastAPI
443/ws → WebSocket
```

### FastAPI
Internal:
```text
0.0.0.0:8000
```

### PostgreSQL
Do not expose publicly.
```text
5432 internal network only
```

### Kafka
Internal network only:
```text
9092
```

### Media gateway
RTSP:
```text
554
```

WebRTC/HTTP delivery:
use configured media gateway ports and proxy them where appropriate.

---

## 6. Camera Ingestion Architecture

### 6.1 Camera configuration

Each camera has:

```json
{
  "camera_id": "CAM-01",
  "name": "Camera 01",
  "location": "Example Junction",
  "latitude": 17.3850,
  "longitude": 78.4867,
  "protocol": "rtsp",
  "stream_url_secret_ref": "cam01_stream",
  "enabled": true
}
```

The actual stream URL must not be returned to ordinary frontend clients.

### 6.2 Stream flow

```text
IP Camera
   │
 RTSP
   │
   ▼
Media Gateway
   │
   ├── Browser delivery
   │
   └── AI frame extraction
           │
           ▼
       AI Workers
```

### 6.3 Browser requirement

Browsers should not be expected to consume arbitrary RTSP URLs directly.

The media layer must provide a browser-compatible transport such as WebRTC or another supported low-latency delivery method.

---

## 7. Ten-Camera Requirement

Camera IDs:

```text
CAM-01
CAM-02
CAM-03
CAM-04
CAM-05
CAM-06
CAM-07
CAM-08
CAM-09
CAM-10
```

The backend must treat them as independent resources.

Requirements:
- one stream failure must not kill other streams;
- each camera has independent health state;
- each camera has independent AI processing;
- camera configuration must be data-driven;
- adding CAM-11 must not require frontend code changes.

---

## 8. AI Processing Pipeline

### 8.1 Frame processing

```text
Live stream
    ↓
Frame sampling
    ↓
OpenCV preprocessing
    ↓
YOLO vehicle detection
    ↓
Plate region detection
    ↓
Crop / perspective preprocessing
    ↓
PaddleOCR
    ↓
Normalization
    ↓
Confidence scoring
    ↓
Event generation
```

### 8.2 Frame-rate strategy

Do not process every camera frame if hardware cannot support it.

Configurable:
```text
camera_fps
ai_fps
resolution
batch_size
confidence_threshold
```

Example:
```text
Camera: 25 FPS
AI inference: 5 FPS
```

The UI can still display the full browser stream while AI inference operates at a lower rate.

---

## 9. OCR Confidence and Re-checking

For every recognition:

```text
raw OCR
   ↓
normalize
   ↓
confidence threshold
   ├── high → accept
   └── low → re-check
                ↓
             alternate preprocessing
                ↓
             second OCR pass
```

Store:
- raw text;
- normalized text;
- confidence;
- OCR engine version;
- preprocessing profile;
- re-check count.

Do not silently convert low-confidence recognition into a high-confidence record.

---

## 10. Event Model

Canonical detection event:

```json
{
  "event_id": "uuid",
  "camera_id": "CAM-01",
  "timestamp": "ISO-8601",
  "plate_number": "TS09AB1234",
  "plate_confidence": 0.964,
  "vehicle_confidence": 0.982,
  "vehicle_class": "car",
  "latitude": 17.3850,
  "longitude": 78.4867,
  "evidence_ref": "object-storage-key"
}
```

---

## 11. Kafka Topics

For scale-out deployment:

```text
traffic.camera.status
traffic.frames.metadata
traffic.vehicle.detected
traffic.plate.detected
traffic.ocr.result
traffic.alert.created
traffic.tracking.updated
traffic.audit.events
```

Suggested event partition key:
```text
camera_id
```

For trajectory processing, a normalized plate identifier can be used where legally and technically appropriate.

For the earliest MVP, Kafka can be introduced after the direct FastAPI/database path is stable. The architecture must keep event contracts stable so Kafka can replace in-process queues without rewriting the UI.

---

## 12. Database Design

### 12.1 users

```text
id UUID PK
officer_id VARCHAR UNIQUE
password_hash TEXT
name VARCHAR
role_id FK
is_active BOOLEAN
created_at TIMESTAMP
last_login_at TIMESTAMP
```

### 12.2 roles

```text
id UUID PK
name VARCHAR UNIQUE
```

### 12.3 cameras

```text
id UUID PK
camera_id VARCHAR UNIQUE
name VARCHAR
location VARCHAR
latitude DOUBLE PRECISION
longitude DOUBLE PRECISION
protocol VARCHAR
stream_secret_ref TEXT
enabled BOOLEAN
status VARCHAR
last_heartbeat TIMESTAMP
created_at TIMESTAMP
updated_at TIMESTAMP
```

### 12.4 vehicle_detections

```text
id UUID PK
camera_id UUID FK
detected_at TIMESTAMP
vehicle_class VARCHAR
vehicle_confidence REAL
plate_number VARCHAR
plate_confidence REAL
evidence_ref TEXT
created_at TIMESTAMP
```

Indexes:
```text
plate_number
detected_at
camera_id
(camera_id, detected_at)
(plate_number, detected_at)
```

### 12.5 camera_health_events

```text
id UUID PK
camera_id UUID FK
status VARCHAR
latency_ms INTEGER
error_code VARCHAR
recorded_at TIMESTAMP
```

### 12.6 journeys

```text
id UUID PK
plate_number VARCHAR
start_time TIMESTAMP
end_time TIMESTAMP
confidence REAL
created_at TIMESTAMP
```

### 12.7 journey_events

```text
id UUID PK
journey_id UUID FK
detection_id UUID FK
sequence_number INTEGER
```

### 12.8 alerts

```text
id UUID PK
type VARCHAR
severity VARCHAR
plate_number VARCHAR
camera_id UUID FK
status VARCHAR
created_at TIMESTAMP
resolved_at TIMESTAMP
resolved_by UUID
evidence_ref TEXT
```

### 12.9 blacklist_entries

```text
id UUID PK
plate_number VARCHAR UNIQUE
reason TEXT
severity VARCHAR
active BOOLEAN
created_at TIMESTAMP
updated_at TIMESTAMP
```

### 12.10 audit_logs

```text
id UUID PK
user_id UUID FK
action VARCHAR
resource_type VARCHAR
resource_id VARCHAR
result VARCHAR
ip_address INET
created_at TIMESTAMP
metadata JSONB
```

---

## 13. PostGIS

Use PostGIS for:
- camera points;
- detection points;
- trajectory geometry;
- spatial queries;
- route proximity;
- map-oriented analytics.

Example logical fields:
```text
camera.location GEOGRAPHY(Point, 4326)
detection.location GEOGRAPHY(Point, 4326)
journey.path GEOMETRY(LineString, 4326)
```

---

## 14. Trajectory Engine

### Input
Chronological detections:

```text
CAM-02 @ 10:01
CAM-05 @ 10:06
CAM-07 @ 10:11
```

### Processing
1. Normalize plate number.
2. Filter low-confidence events.
3. Sort by timestamp.
4. Validate plausible temporal sequence.
5. Attach camera coordinates.
6. Create ordered journey events.
7. Generate a map line/segments.
8. Assign journey confidence.

### Important constraint
A trajectory is an inference from detections. If the gap between observations is too large or physically implausible, mark the segment uncertain instead of inventing a route.

---

## 15. Alert Engine

Rules:

```text
IF plate_number ∈ active_blacklist
THEN CRITICAL alert

IF same plate appears at N cameras within T minutes
THEN REVIEW alert

IF camera heartbeat expires
THEN CAMERA_OFFLINE alert

IF OCR confidence < threshold repeatedly
THEN LOW_CONFIDENCE alert
```

All rules should be configurable.

---

## 16. REST API

### Authentication

```text
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

### Cameras

```text
GET    /api/cameras
GET    /api/cameras/{camera_id}
POST   /api/cameras
PATCH  /api/cameras/{camera_id}
DELETE /api/cameras/{camera_id}
GET    /api/cameras/{camera_id}/health
```

### Vehicles

```text
GET /api/vehicles/search?plate=TS09AB1234
GET /api/vehicles/{plate}/detections
GET /api/vehicles/{plate}/journey
```

### Alerts

```text
GET   /api/alerts
GET   /api/alerts/{alert_id}
PATCH /api/alerts/{alert_id}
```

### Analytics

```text
GET /api/analytics/overview
GET /api/analytics/hourly
GET /api/analytics/cameras
GET /api/analytics/alerts
```

### Audit

```text
GET /api/audit
```

---

## 17. WebSocket API

Suggested endpoint:

```text
/ws/operations
```

Events:

```json
{
  "type": "vehicle_detection",
  "camera_id": "CAM-03",
  "plate_number": "TS09AB1234",
  "confidence": 0.97,
  "timestamp": "2026-09-01T12:40:00Z"
}
```

Other event types:
```text
camera_status
alert_created
alert_updated
vehicle_detection
trajectory_updated
system_health
```

Frontend should update relevant components without polling every few seconds.

---

## 18. Frontend Architecture

Recommended routes:

```text
/login
/dashboard
/cameras
/cameras/:cameraId
/vehicles
/vehicles/:plate
/vehicles/:plate/trajectory
/alerts
/analytics
/settings/cameras
/settings/users
/audit
```

Components:

```text
AppShell
Sidebar
TopBar
StatCard
CameraCard
CameraGrid
VehicleSearch
VehicleDetectionTable
AlertCard
MapView
TrajectoryPanel
AnalyticsChart
ProtectedRoute
RoleGuard
SystemStatus
```

---

## 19. State Management

For MVP:
- React Context for authentication/session;
- local component state for simple UI;
- API service layer for backend calls;
- WebSocket hook for live events.

If state complexity grows, introduce a dedicated state library.

---

## 20. Authentication Security

Login flow:

```text
Browser
  │
  │ POST credentials
  ▼
FastAPI
  │
  ├── verify password hash
  ├── verify active user
  ├── create access token/session
  └── audit login
  │
  ▼
Browser
```

Production requirements:
- HTTPS;
- secure cookies if cookie sessions are used;
- CSRF protection for cookie-based mutation requests;
- short-lived access tokens if JWT is used;
- refresh-token rotation if implemented;
- login rate limiting;
- no plaintext passwords.

---

## 21. Environment Variables

Example:

```env
APP_ENV=development

DATABASE_URL=postgresql+psycopg://user:password@postgres:5432/traffic_ai

JWT_SECRET=replace_with_secure_random_secret
JWT_EXPIRE_MINUTES=30

KAFKA_BOOTSTRAP_SERVERS=kafka:9092

MEDIAMTX_HOST=mediamtx

FRONTEND_ORIGIN=http://localhost:5173

YOLO_MODEL_PATH=models/vehicle.pt
OCR_LANG=en

PLATE_CONFIDENCE_THRESHOLD=0.70
VEHICLE_CONFIDENCE_THRESHOLD=0.50
```

Never commit real secrets.

---

## 22. Deployment Architecture (Native & Production)

Core runtime components:

```text
frontend (Vite / React 18 on port 5173 or Nginx static bundle)
backend (FastAPI / Uvicorn ASGI on port 8000)
database (SQLite traffic_ai.db or PostgreSQL / Supabase)
camera streams (RTSP / WebRTC / HLS / Snapshots)
ai-worker (YOLOv8 + PaddleOCR processing loop)
```

The system is optimized for direct native execution:
- **Backend:** `python run.py` (FastAPI/Uvicorn)
- **Frontend:** `npm run dev` (Vite)
- **Database:** Automatic SQLite initialization on startup (zero external configuration required)

For the SIH demonstration, a single local developer machine runs the entire stack smoothly.

---

## 23. Browser Accessibility

### Development
```text
http://localhost:5173
```

### LAN demonstration
Frontend and backend must bind to:
```text
0.0.0.0
```

Example:
```text
http://192.168.x.x
```

Other devices on the same network can then access the application, subject to firewall/router rules.

### Production
Use:
```text
https://traffic-ai-engine.example
```

with:
- DNS;
- HTTPS certificate;
- reverse proxy;
- protected APIs;
- private database;
- controlled media access.

---

## 24. Camera Security

Never send:

```text
rtsp://username:password@camera-ip/...
```

to the browser.

Instead:
```text
Browser → authenticated media gateway → camera
```

Camera credentials must remain server-side.

---

## 25. Logging and Observability

Backend logs:
- startup/shutdown;
- API request errors;
- authentication failures;
- camera connection changes;
- AI worker failures;
- Kafka failures;
- database failures.

Metrics:
- camera uptime;
- stream latency;
- frames processed;
- inference FPS;
- OCR confidence;
- alerts/hour;
- API latency;
- WebSocket clients;
- queue depth.

---

## 26. Error Handling

Standard API error shape:

```json
{
  "error": {
    "code": "CAMERA_OFFLINE",
    "message": "Camera CAM-03 is currently unavailable",
    "request_id": "uuid"
  }
}
```

Do not expose stack traces or secrets to clients.

---

## 27. Testing Requirements

### Unit tests
- plate normalization;
- OCR confidence logic;
- alert rules;
- trajectory sequencing;
- permission checks.

### Integration tests
- login;
- camera CRUD;
- vehicle search;
- detection persistence;
- alert generation;
- WebSocket events.

### Stream tests
- connect/disconnect;
- reconnect;
- malformed stream;
- ten-camera concurrency.

### AI tests
Use a controlled dataset to measure:
- vehicle detection;
- plate detection;
- OCR accuracy;
- false positives;
- confidence thresholds.

### UI tests
- login;
- protected routes;
- camera wall;
- search;
- map;
- alert acknowledgement;
- responsive layout.

---

## 28. Performance Targets

Prototype targets:
- 10 independently monitored camera channels.
- API p95 target <1 second for ordinary indexed reads.
- Vehicle search p95 target <1 second for normal indexed queries.
- Live-stream latency target: low latency subject to camera/network/media stack.
- UI live-event update target: within approximately 1–2 seconds under normal conditions.
- Camera failure isolation: 100% of unaffected camera services continue.

AI throughput depends on GPU/CPU and model resolution.

---

## 29. Resource Strategy

### CPU
Used for:
- API;
- database;
- media/control operations;
- preprocessing;
- lightweight analytics.

### GPU
Preferred for:
- YOLO inference;
- OCR acceleration where supported.

### RAM
Required for:
- model loading;
- camera buffers;
- Kafka;
- database;
- browser/media gateway.

For a laptop-based SIH demo, run a reduced inference FPS and resolution rather than attempting maximum camera FPS.

---

## 30. SUMO Integration

SUMO is a future/advanced component for traffic simulation.

Proposed flow:

```text
Historical/observed traffic data
        ↓
Traffic demand model
        ↓
SUMO simulation
        ↓
Congestion scenarios
        ↓
Analytics dashboard
```

It should not block the core ANPR/trajectory MVP.

---

## 31. Security Threat Model

Threats:
- credential brute force;
- unauthorized vehicle lookup;
- leaked RTSP credentials;
- API abuse;
- database exposure;
- malicious stream URLs;
- privilege escalation;
- evidence URL guessing;
- insecure WebSocket connections.

Controls:
- rate limiting;
- RBAC;
- input validation;
- URL allowlisting for camera configuration;
- secret storage;
- private database;
- signed/authenticated media access;
- HTTPS/WSS;
- audit logging;
- least privilege.

---

## 32. Data Retention

Retention must be configurable.

Example technical policy structure:

```text
Hot detection metadata → short/medium period
Evidence images/video → shorter configurable period
Aggregated analytics → longer period
Audit logs → organizational policy
```

Actual retention periods must be determined by the authorized deploying organization and applicable law/policy.

---

## 33. CI/CD

Recommended pipeline:

```text
git push
   ↓
lint
   ↓
unit tests
   ↓
build frontend
   ↓
build backend image
   ↓
integration tests
   ↓
deploy staging
   ↓
manual acceptance
   ↓
production
```

---

## 34. Implementation Phases

### Phase 1 — Foundation
- React application
- Login UI
- Dashboard shell
- FastAPI
- database abstraction
- API structure

### Phase 2 — Real backend
- PostgreSQL/PostGIS
- real authentication
- RBAC
- camera CRUD
- audit logs

### Phase 3 — Streaming
- MediaMTX
- RTSP configuration
- browser-compatible live playback
- ten-camera wall
- camera health/reconnect

### Phase 4 — AI
- YOLO
- plate detection
- PaddleOCR
- confidence/re-check pipeline
- detection persistence

### Phase 5 — Intelligence
- vehicle search
- trajectory stitching
- Kafka event architecture
- alerts

### Phase 6 — GIS/Analytics
- Leaflet
- camera map
- journey map
- analytics

### Phase 7 — Deployment
- Native local deployment
- LAN access
- HTTPS/cloud deployment
- monitoring
- SIH demo hardening

---

## 35. Definition of Done

The engineering implementation is complete when:

- all core APIs are implemented and tested;
- PostgreSQL/PostGIS is the production database;
- authentication/RBAC is server enforced;
- ten cameras can be configured;
- actual RTSP feeds can be ingested;
- browser-compatible live feeds work;
- camera failures are isolated and visible;
- YOLO detects vehicles;
- plate detection/OCR produces confidence-scored events;
- events are persisted;
- vehicle search works;
- trajectory reconstruction works from multiple camera detections;
- Leaflet renders camera locations and journeys;
- blacklist alerts work;
- analytics work from real stored events;
- audit logs work;
- application is deployable on a LAN;
- application is deployable behind HTTPS;
- secrets are externalized;
- documentation and environment templates are included.

---

## 36. Engineering Principles

1. Do not fake live camera status.
2. Do not represent prerecorded video as live.
3. Do not expose camera credentials to browsers.
4. Do not trust frontend authorization.
5. Do not claim OCR certainty without confidence.
6. Do not create a trajectory when evidence is insufficient.
7. Isolate camera failures.
8. Keep camera configuration data-driven.
9. Keep AI processing asynchronous.
10. Preserve auditability of sensitive operations.
11. Keep privacy and retention configurable.
12. Build the MVP so later scale-out does not require a complete rewrite.

---

## 37. Source Traceability

The technical choices and requirements are based primarily on the submitted SIH presentation:

- Problem Statement ID 26127: City-Wide AI Engine for Multi-Camera ANPR Trajectory Tracking and Urban Traffic Analytics.
- Proposed centralized AI platform with OCR, trajectory reconstruction and live analytics dashboard.
- Query-based city-wide journey reconstruction.
- Shared event bus concept.
- Confidence-scored/ensemble OCR.
- Graph-based trajectory stitching.
- Existing camera infrastructure.
- OpenCV, YOLOv8, PaddleOCR, FastAPI, Kafka, PostgreSQL, React, Leaflet and SUMO.
- Identified risks around OCR, camera variation, data volume and privacy.
- Proposed mitigations including OCR re-checks, standardized camera handling, retention rules, permissions and activity logs.

The supplied SIH PPT does not specify every implementation detail in this TRD (for example, exact API schemas, table structures, WebSocket contracts and deployment topology). Those sections are engineering elaborations required to turn the proposal into a working prototype and are explicitly presented as implementation requirements rather than claims that they appeared verbatim in the PPT.
