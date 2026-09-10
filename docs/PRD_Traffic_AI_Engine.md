# Product Requirements Document (PRD)
## Traffic AI Engine — City-Wide Multi-Camera ANPR, Trajectory Tracking & Urban Traffic Analytics

**Team:** Mind Mesh  
**SIH Problem Statement ID:** 26127  
**Theme:** Smart Automation  
**Category:** Software  
**Document status:** Product baseline for working prototype and SIH demonstration  
**Version:** 1.0  
**Date:** 1 September 2026

---

## 1. Executive Summary

Traffic AI Engine is a centralized web platform intended to unify existing CCTV/ANPR camera feeds into one operational intelligence system. The product addresses the problem that camera systems often operate independently, making it difficult to reconstruct a vehicle's movement across multiple locations and analyze city-wide traffic.

The proposed platform combines:
- live multi-camera ingestion;
- vehicle and number-plate detection;
- OCR with confidence scoring and re-checks;
- cross-camera trajectory reconstruction;
- GIS visualization;
- blacklist/suspicious-vehicle alerts;
- vehicle search;
- traffic analytics;
- role-based access and audit logging.

The SIH proposal specifies OpenCV, YOLOv8, PaddleOCR, Python/FastAPI, Apache Kafka, PostgreSQL, React, Leaflet and SUMO as the intended technology stack.

For the working prototype, the system must support ten configured camera channels. The current development environment has no physical cameras, so the camera subsystem must be designed around real RTSP sources and must never represent prerecorded files as live cameras. Actual RTSP sources can be connected later without redesigning the application.

---

## 2. Problem Statement

Modern cities have many CCTV and ANPR cameras, but systems may work independently and cannot reliably track vehicles across different locations. This creates difficulty in:
- identifying vehicle movement patterns;
- investigating suspicious vehicles;
- correlating detections across cameras;
- analyzing traffic efficiently;
- producing a unified operational view.

Traffic AI Engine replaces isolated camera silos with a shared event-driven platform and a single dashboard for tracking, analytics and alerts.

---

## 3. Product Vision

Create a scalable, secure and operator-friendly traffic intelligence platform in which an authorized officer can:
1. authenticate securely;
2. monitor the health and availability of the camera network;
3. view live feeds;
4. detect and recognize vehicles and number plates;
5. search a registration number;
6. reconstruct detections across cameras;
7. view the trajectory on a GIS map;
8. receive and investigate alerts;
9. inspect traffic analytics;
10. review access/activity history.

---

## 4. Goals

### 4.1 Primary goals
- Centralize ten camera channels in the prototype.
- Provide genuine live-stream support using RTSP/WebRTC-compatible infrastructure.
- Provide a responsive web application accessible through Chrome on other devices after deployment.
- Implement ANPR using vehicle/plate detection and OCR.
- Store detections as structured events.
- Reconstruct a vehicle journey from camera hits.
- Visualize cameras and trajectories on a GIS map.
- Provide blacklist and suspicious-vehicle alerts.
- Provide search and analytics.
- Protect sensitive vehicle-tracking data with authentication, authorization and audit logs.

### 4.2 Secondary goals
- Make camera onboarding configuration-driven.
- Support gradual expansion beyond ten cameras.
- Provide health monitoring for camera streams.
- Support low-confidence OCR re-checking.
- Keep the UI suitable for an SIH command-center demonstration.
- Keep deployment portable across a local LAN and cloud-hosted environment.

---

## 5. Non-Goals / Boundaries

The prototype will not:
- claim to be an official Government of India portal;
- replace a certified police/RTO operational system;
- make autonomous enforcement decisions;
- identify a person from a vehicle plate without an authorized legal data source;
- disguise prerecorded videos as live feeds;
- assume that ten physical cameras exist when they do not;
- guarantee perfect OCR under poor visibility;
- expose sensitive vehicle-tracking data publicly.

The system is an engineering prototype for demonstration and validation.

---

## 6. Target Users

### 6.1 Traffic Police / Authorized Officer
Needs:
- live monitoring;
- vehicle lookup;
- trajectory reconstruction;
- alerts;
- camera health;
- investigation history.

### 6.2 City Administration
Needs:
- traffic patterns;
- congestion indicators;
- camera/network health;
- aggregate analytics.

### 6.3 RTO / Authorized Transport Personnel
Needs:
- vehicle detection analytics;
- authorized vehicle queries;
- traffic movement statistics.

### 6.4 System Administrator
Needs:
- officer/role management;
- camera configuration;
- blacklist management;
- system health;
- audit logs.

---

## 7. User Roles and Permissions

| Capability | Officer | Analyst | Administrator |
|---|---:|---:|---:|
| Login | Yes | Yes | Yes |
| View dashboard | Yes | Yes | Yes |
| View live cameras | Yes | Yes | Yes |
| Search vehicles | Yes | Yes | Yes |
| View trajectories | Yes | Yes | Yes |
| View alerts | Yes | Yes | Yes |
| View analytics | Yes | Yes | Yes |
| Configure cameras | No | No | Yes |
| Manage blacklist | No | Optional | Yes |
| Manage users | No | No | Yes |
| View audit logs | Limited | Limited | Yes |

Permissions must be enforced server-side; hiding a UI button is not considered authorization.

---

## 8. Core User Journeys

### 8.1 Officer login
1. Officer opens the web application.
2. Login page displays secure access messaging.
3. Officer submits credentials.
4. Backend authenticates the account.
5. Backend issues a secure session/token.
6. Dashboard loads according to role.
7. Login activity is recorded.

### 8.2 Monitor camera network
1. Officer opens Camera Network.
2. System displays ten configured camera cards.
3. Each card shows stream status, location and latest detection.
4. Live channels are rendered through a browser-compatible stream.
5. Failed streams are marked offline/degraded.
6. Health changes are pushed to the UI.

### 8.3 Search a vehicle
1. Officer enters a registration number.
2. Backend normalizes the input.
3. Matching detections are retrieved.
4. Results show camera, timestamp, confidence and location.
5. Officer can open the trajectory view.
6. Authorized access is logged.

### 8.4 Investigate a suspicious vehicle
1. A detection matches a configured blacklist or rule.
2. Alert engine creates an alert.
3. Operator sees severity and evidence.
4. Operator opens vehicle history.
5. System displays recent camera hits and trajectory.
6. Investigation activity is recorded.

---

## 9. Functional Requirements

### FR-01 Authentication
- Login with officer ID and password.
- Passwords must be stored as secure hashes.
- Authentication failures must not disclose whether an ID exists.
- Sessions/tokens must expire.
- Logout must invalidate the client session.
- Authentication events must be logged.

### FR-02 Role-based authorization
- Every protected API must validate identity and role.
- Administrative endpoints must be restricted.
- Unauthorized access must return an appropriate HTTP error.

### FR-03 Camera management
- Support at least ten camera records.
- Each camera must have:
  - camera ID;
  - display name;
  - location;
  - latitude/longitude;
  - stream URL/reference;
  - protocol;
  - status;
  - last heartbeat;
  - enabled/disabled state.
- Camera URLs must not be exposed to unauthorized users.
- Administrator can add/update/disable cameras.

### FR-04 Live streaming
- Accept real RTSP camera sources.
- Use a streaming gateway/media layer to convert/relay streams to browser-compatible delivery.
- The frontend must not attempt to play RTSP directly.
- The UI must display stream health.
- A disconnected stream must show a clear offline/degraded state.
- The architecture must permit ten concurrent camera channels.

### FR-05 Vehicle detection
- Process frames from live camera streams.
- Detect vehicles using the selected computer-vision model.
- Associate detections with camera ID and timestamp.
- Retain model confidence and processing metadata.

### FR-06 Number-plate detection
- Detect plate regions from vehicle frames.
- Crop/normalize plate images before OCR.
- Preserve the source camera and timestamp.

### FR-07 OCR
- Run PaddleOCR or the selected OCR implementation.
- Normalize plate text.
- Store OCR confidence.
- Run multiple OCR checks/re-check low-confidence results.
- Mark uncertain results rather than silently treating them as correct.

### FR-08 Detection event storage
Each detection should contain, where available:
- event ID;
- camera ID;
- plate text;
- OCR confidence;
- vehicle class;
- detection confidence;
- timestamp;
- latitude/longitude;
- frame/evidence reference;
- processing status.

### FR-09 Vehicle search
- Search by normalized registration number.
- Support partial/exact search according to role.
- Return chronological camera hits.
- Provide confidence and evidence references.
- Allow opening a trajectory.

### FR-10 Trajectory reconstruction
- Group detections that likely belong to the same vehicle/plate.
- Order events by time.
- Associate camera nodes with geographic positions.
- Construct a path between sequential camera hits.
- Display uncertainty where detections are weak or gaps are large.
- Do not claim physical continuity when evidence is insufficient.

### FR-11 GIS map
- Display camera locations.
- Display selected vehicle trajectory.
- Display detection points.
- Support zoom/pan.
- Show camera metadata on selection.
- Provide clear map legends.

### FR-12 Alerts
Initial alert types:
- blacklisted plate;
- repeated camera hits;
- low-confidence critical detection;
- camera offline/degraded;
- configurable rule-based anomalies.

Alert fields:
- alert ID;
- severity;
- type;
- plate/camera;
- created time;
- status;
- evidence;
- assigned/resolved metadata.

### FR-13 Analytics
Minimum prototype analytics:
- vehicles detected by hour;
- detections by camera;
- OCR accuracy/confidence distribution;
- alert counts;
- camera uptime/health;
- top detected routes/locations where sufficient data exists.

### FR-14 Audit logging
Log:
- login/logout;
- failed login;
- vehicle search;
- trajectory access;
- alert access;
- blacklist changes;
- camera configuration changes;
- administrative actions.

Audit logs should include actor, action, timestamp, result and relevant resource ID.

### FR-15 Responsive web UI
- Chrome desktop support.
- Tablet/mobile responsive behavior.
- Dashboard must remain usable at common screen sizes.
- Critical operational controls must be keyboard accessible.

---

## 10. UI / UX Requirements

### Visual direction
The interface should feel like a professional Indian public-sector command-and-control application without falsely representing itself as an official government website.

Design characteristics:
- restrained government/command-center visual language;
- clear information hierarchy;
- strong contrast;
- Indian map/location context;
- bilingual-ready text architecture;
- formal typography;
- accessibility-conscious colors;
- minimal decorative effects.

### Primary screens
1. Secure Login
2. Operations Dashboard
3. Live Camera Wall
4. Camera Detail
5. Vehicle Search
6. Vehicle Profile/Detection History
7. Trajectory & GIS
8. Alerts
9. Analytics
10. Camera Network Administration
11. User/Role Administration
12. Audit Logs
13. System Health

### Camera wall
For ten cameras:
- 2x5 or responsive grid;
- camera ID and location;
- live/offline state;
- latest plate detection;
- OCR confidence;
- alert indicator;
- full-screen/detail action.

---

## 11. Data Requirements

Core entities:
- User
- Role
- Camera
- CameraHealthEvent
- VehicleDetection
- PlateRecognition
- VehicleJourney
- JourneyEvent
- Alert
- BlacklistEntry
- AuditLog

Sensitive data must be minimized and retained only as permitted by applicable organizational/legal requirements.

---

## 12. Performance Requirements

Target prototype requirements:
- Dashboard initial API response: preferably <500 ms excluding network conditions.
- Vehicle search API: preferably <1 s for indexed normal searches.
- Live camera display: low-latency browser stream where infrastructure permits.
- WebSocket events: near-real-time delivery.
- Ten configured camera channels must be independently monitored.
- AI processing may be asynchronous; the UI must never freeze waiting for OCR.

These are engineering targets, not guarantees for arbitrary hardware/network conditions.

---

## 13. Reliability Requirements

- Camera failure must not crash the backend.
- One bad stream must not stop other camera streams.
- AI processing failures must be isolated per frame/camera.
- Failed events should be observable through logs/metrics.
- Backend restart must preserve persisted data.
- Camera health state must recover automatically when a stream returns.

---

## 14. Security and Privacy Requirements

- HTTPS in production.
- Strong password hashing.
- JWT or secure server-side session authentication.
- Role-based access control.
- Server-side authorization.
- Secure secret management through environment/configuration.
- CORS restricted to trusted origins in production.
- Database credentials never committed to source control.
- Stream credentials never exposed in browser code.
- Rate-limit authentication endpoints.
- Log sensitive access without unnecessarily duplicating sensitive plate data.
- Apply configurable data retention.
- Protect evidence/media endpoints.
- Maintain audit trails for vehicle searches and trajectory access.

---

## 15. Camera/AI Accuracy Requirements

The SIH proposal recognizes OCR limitations caused by low light, weather, blocked plates, different camera quality, angles and frame rates.

Therefore:
- confidence scores are mandatory;
- low-confidence recognition must be flagged;
- multiple OCR checks should be used;
- plate normalization should account for common OCR errors;
- camera-specific configuration should be possible;
- analytics must distinguish detections from high-confidence recognized plates.

The product must not present 100% OCR accuracy as a guaranteed result.

---

## 16. Deployment Requirements

### Development
- React/Vite frontend.
- FastAPI backend.
- Local development database initially allowed.
- Dockerization recommended.

### Demonstration/LAN
- Backend bound to an accessible network interface.
- Frontend served through a web server.
- Other devices connect using the host machine's LAN address.
- Camera/media services run on the server or reachable infrastructure.

### Cloud
- HTTPS domain.
- React frontend behind reverse proxy/CDN.
- FastAPI behind reverse proxy.
- PostgreSQL managed/self-hosted.
- Media/RTSP infrastructure separated from public web application where appropriate.
- Firewall rules restrict camera and database ports.

---

## 17. Acceptance Criteria

The prototype is considered functionally complete when:

1. An authorized user can log in.
2. Unauthorized users cannot access protected APIs.
3. Ten camera records can be configured.
4. Real RTSP streams can be connected without frontend redesign.
5. Browser-compatible live feeds render.
6. A camera going offline is reflected in the dashboard.
7. Vehicle/plate detections can be generated from a live source.
8. OCR results include confidence.
9. Detections persist in the database.
10. Registration search returns matching detections.
11. A selected vehicle can be visualized on a GIS map.
12. Sequential camera detections can form a journey/trajectory.
13. Blacklist matches create alerts.
14. Analytics are generated from stored events.
15. Audit logs record sensitive actions.
16. The application can be accessed from another Chrome device after deployment.
17. No prerecorded video is falsely labeled as a live camera.
18. Failure of one camera does not terminate the complete system.

---

## 18. MVP vs Future Scope

### SIH MVP
- Authentication/RBAC
- Ten camera configuration
- Live RTSP/WebRTC architecture
- Vehicle + plate detection
- OCR
- Detection database
- Vehicle search
- Basic trajectory stitching
- Leaflet map
- Blacklist alerts
- Dashboard
- Basic analytics
- Audit logs

### Future
- city-scale Kafka deployment;
- advanced multi-object re-identification;
- distributed GPU inference;
- automated camera calibration;
- advanced congestion prediction;
- SUMO digital-twin integration;
- stronger evidence management;
- multi-city federation;
- multilingual UI;
- advanced anomaly detection.

---

## 19. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| OCR errors | Multi-pass OCR, confidence thresholding, re-checks |
| Low light/weather | preprocessing and confidence flags |
| Different camera formats | standard media gateway and camera profiles |
| Large data volume | retention tiers and indexing |
| Stream failure | isolated stream workers and health monitoring |
| GPU limitations | asynchronous inference and configurable FPS |
| Privacy/legal concerns | RBAC, audit logs, retention controls |
| Network failure | local buffering/health status |
| False alerts | confidence thresholds and operator review |

---

## 20. Success Metrics

Prototype success:
- 10 camera channels configurable.
- Live stream availability observable per camera.
- Detection events correctly associated with camera/time.
- OCR confidence available for recognized plates.
- Searchable vehicle history.
- Cross-camera journey visualization.
- Alert generation.
- Dashboard usable from Chrome on a second device.
- No single camera failure brings down the platform.

---

## 21. Traceability to SIH Proposal

The product directly implements the proposal's core concepts:
- centralized AI platform unifying CCTV/ANPR feeds;
- OCR engine;
- trajectory reconstruction;
- live analytics dashboard;
- query-based city-wide plate journey;
- shared event bus concept;
- ensemble/confidence-based OCR;
- graph-based trajectory stitching;
- existing-camera integration;
- permissions and activity logs.

Source basis: SIH PPT, Problem Statement 26127, Team Mind Mesh.
