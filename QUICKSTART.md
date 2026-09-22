# Quick Start Guide - Traffic AI Engine

A step-by-step guide to running the Traffic AI Engine locally using Python and Node.js.

---

## System Requirements

- **Operating System:** Windows 10/11, macOS, or Linux
- **Python:** 3.9+ (Python 3.10 - 3.12 recommended)
- **Node.js:** 18.x or higher with npm
- **Database:** SQLite (built-in, zero configuration needed) or PostgreSQL / Supabase
- **Internet Connection:** For downloading dependencies and accessing live camera streams

---

## Quick Start (3 Steps)

### Step 1: Start the Python Backend

Open a terminal (PowerShell on Windows, or bash on Linux/macOS):

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment:
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows Command Prompt:
# .\venv\Scripts\activate.bat
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Seed demo users and initial database state
python seed_admin.py
python seed_demo_users.py

# Start backend server
python run.py
```

> **Backend Status:** Runs at **http://localhost:8000**  
> **Interactive API Docs (Swagger):** **http://localhost:8000/docs**  
> **Alternative API Docs (ReDoc):** **http://localhost:8000/redoc**

---

### Step 2: Start the Frontend UI

Open a **new separate terminal**:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (only needed first time)
npm install

# Start Vite development server
npm run dev
```

> **Frontend Application:** Runs at **http://localhost:5173**

---

### Step 3: Log In & Explore

Navigate to **http://localhost:5173/login** in your web browser.

#### Demo Credentials:
| Role | Officer ID / Username | Password | Purpose |
|---|---|---|---|
| **Super Admin** | `superadmin` | `admin123` | Full administrative control & user management |
| **Traffic Officer** | `officer` | `officer123` | ANPR searches, vehicle tracking, alerts |
| **Control Room** | `control` | `control123` | Real-time camera wall monitoring & alerts |
| **Analyst** | `analyst` | `analyst123` | Traffic flow analysis & statistical reports |

---

## Application Navigation

The frontend includes 8 dedicated dashboard modules accessible via the sidebar:

1. **Dashboard (`/`):** Live telemetry overview, active cameras, 24-hour detection counts, and recent alert events.
2. **Live Camera Wall (`/cameras`):** Multi-feed live CCTV grid with WebRTC (WHEP), HLS streaming, live auto-refresh snapshots, fullscreen mode, and stream status diagnostics.
3. **Find Vehicle (`/find-vehicle`):** License plate lookup, camera detection history, snapshot evidence, speed estimations, and manual blacklist flagging.
4. **Track Vehicle (`/track`):** Chronological multi-camera trajectory tracking that stitches vehicle movements across intersections.
5. **Live GIS Map (`/map`):** Leaflet interactive map displaying camera positions, real-time status indicators, and geographic coverage.
6. **Traffic Analytics (`/analytics`):** Charts for hourly traffic volume, vehicle classifications (cars, two-wheelers, trucks, buses), peak-hour congestion, and camera throughput.
7. **Alerts & Incidents (`/alerts`):** Real-time violation alerts (blacklist match, speeding, unauthorized access) with severity tags and status workflows (New / Acknowledged / Resolved).
8. **Blacklist Management (`/blacklist`):** Manage hotlist vehicles with plate numbers, descriptions, violation reasons, and automated matching.

---

## Project Structure

```
AI-Traffic-Engine/
├── backend/                       # FastAPI Backend
│   ├── app/
│   │   ├── main.py               # Application entry point & middleware
│   │   ├── database.py           # Database connection & session factory
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── routers/              # API routers (auth, cameras, search, etc.)
│   │   ├── ai/                   # YOLOv8 detection & PaddleOCR recognition
│   │   ├── tracking/             # Trajectory reconstruction logic
│   │   └── core/                 # Security (JWT/bcrypt), configuration, logger
│   ├── snapshots/                # Live camera frame cache (.jpg files)
│   ├── workers/                  # Background live processor workers
│   ├── requirements.txt          # Python package requirements
│   ├── run.py                    # Backend server launcher
│   ├── seed_admin.py             # Admin user seeder
│   ├── seed_demo_users.py        # Demo role accounts seeder
│   ├── seed_real_cameras.py      # Camera database seeder
│   └── traffic_ai.db             # Local SQLite database
│
├── frontend/                      # React 18 + Vite Frontend
│   ├── src/
│   │   ├── pages/                # All 9 dashboard pages
│   │   ├── components/           # Stream players (WebRTCPlayer, HlsPlayer), cards
│   │   ├── layouts/              # Responsive sidebar & navigation header
│   │   ├── services/             # Axios API client
│   │   ├── App.jsx               # App routing & protected route guard
│   │   ├── index.css             # Design tokens & global CSS
│   │   └── main.jsx              # React mounting point
│   ├── package.json              # Node dependencies
│   └── vite.config.js            # Vite configuration
│
├── database/                      # SQL schema definitions
├── docs/                          # PRD & TRD technical documents
└── test_api.py                    # Comprehensive automated API test suite
```

---

## Completed Features Status

- [x] **User Authentication & Authorization (JWT + RBAC)**
- [x] **Camera Management & Multi-Protocol Streaming (RTSP, WebRTC/WHEP, HLS, Snapshots)**
- [x] **Database Schema & Models (SQLite / PostgreSQL with PostGIS support)**
- [x] **Vehicle Detection (YOLOv8)**
- [x] **License Plate Recognition (PaddleOCR)**
- [x] **Cross-Camera Trajectory Reconstruction**
- [x] **Automated Blacklist & Stolen Vehicle Alerting**
- [x] **Interactive GIS Map Visualization (Leaflet)**
- [x] **Comprehensive Traffic Analytics & Charting**
- [x] **Responsive Modern Web Interface (React 18 + Vite)**

---

## Key API Endpoints

### Authentication
- `POST /api/auth/login` - Officer login (returns JWT token and profile)
- `POST /api/auth/logout` - Invalidate session
- `POST /api/auth/register` - Create user account (Admin only)
- `GET /api/auth/me` - Current authenticated user details

### Cameras & Feeds
- `GET /api/cameras/` - List all cameras with live status
- `GET /api/cameras/{camera_id}` - Get camera details and RTSP / WebRTC URLs
- `POST /api/cameras/` - Add new camera (Admin)
- `PUT /api/cameras/{camera_id}` - Update camera settings
- `DELETE /api/cameras/{camera_id}` - Remove camera
- `GET /api/cameras/{camera_id}/snapshot` - Get latest snapshot frame
- `GET /api/ingest` - Sentinel-compliant stream ingest catalogue

### Vehicle Detection & Search
- `GET /api/detection/` - List detections with confidence scores
- `GET /api/search/vehicles` - Search detections by license plate
- `GET /api/search/history/{vehicle_id}` - Historical sightings for vehicle

### Trajectories
- `GET /api/trajectories/journeys` - List reconstructed journeys
- `GET /api/trajectories/journey/{id}` - Journey details with chronological sequence
- `GET /api/trajectories/map-data` - Geospatial coordinates for GIS mapping

### Alerts & Blacklist
- `GET /api/alerts/` - List active alerts
- `PUT /api/alerts/{id}` - Update alert status (acknowledged/resolved)
- `GET /api/blacklist/` - List blacklisted plates
- `POST /api/blacklist/` - Add vehicle to blacklist

### Analytics
- `GET /api/analytics/dashboard` - High-level metrics for dashboard cards
- `GET /api/analytics/detections/by-camera` - Camera throughput
- `GET /api/analytics/patterns` - Traffic flow patterns

---

## Automated Verification

Run the test suite from the repository root to validate all API endpoints:

```bash
# Make sure backend is running on port 8000, then run:
python test_api.py
```

Expected output:
```
[INFO] === TESTING AUTHENTICATION ===
  [PASS] POST /auth/login - Logged in as superadmin (Super Admin)
  [PASS] GET /auth/me - Current officer: superadmin
...
[INFO] ALL CORE API TESTS PASSED SUCCESSFULLY!
```

---

## Configuration (`backend/.env`)

Configuration can be tuned in `backend/.env` (defaults are pre-configured):

```bash
# Environment
FASTAPI_ENV=development
FASTAPI_DEBUG=true
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# Database (Default: SQLite local database file)
DATABASE_URL=sqlite:///./traffic_ai.db
# Or use PostgreSQL / Supabase:
# DATABASE_URL=postgresql://user:password@host:5432/traffic_ai

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_EXPIRATION_HOURS=24

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# AI Models
YOLO_MODEL=yolov8n
OCR_ENGINE=paddleocr

# Sentinel Streaming Feeds (Live cameras)
STREAM_EMAIL=your_email@example.com
STREAM_PASSWORD=your_stream_key
STREAM_HOST=103.250.160.189
```

---

## Troubleshooting

### Port 8000 or 5173 is already in use
- Check what process is using the port:
  ```powershell
  # On Windows PowerShell:
  Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess
  ```
- Or terminate the old process:
  ```powershell
  Stop-Process -Id <PID> -Force
  ```

### Database reset
To reset the SQLite database to clean state:
```bash
cd backend
python reset_db.py
python seed_admin.py
python seed_demo_users.py
python seed_real_cameras.py
```

### Camera feed snapshot loading
- The system automatically serves cached snapshots from `backend/snapshots/` when live WebRTC or RTSP feeds are buffering or offline.
- Run `python backend/check_cams.py` to test live camera connectivity.
