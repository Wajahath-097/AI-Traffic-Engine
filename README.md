# Traffic AI Engine

City-Wide Multi-Camera ANPR, Trajectory Tracking & Urban Traffic Analytics

**Team:** Coding Impasta  
**SIH Problem Statement ID:** 26127  
**Theme:** Smart Automation  

---

## Project Overview

Traffic AI Engine is a centralized intelligent traffic monitoring and analytics platform that unifies CCTV/ANPR camera feeds into a single operational command system. The platform provides:

- **Live Multi-Camera Ingestion:** Direct RTSP, WebRTC (WHEP), HLS streaming, and live frame snapshots.
- **AI Vehicle & Plate Detection:** YOLOv8 for vehicle classification (car, truck, bus, motorbike) and PaddleOCR for high-precision license plate recognition.
- **Cross-Camera Trajectory Reconstruction:** Automatic vehicle journey stitching and timeline generation across city camera networks.
- **Interactive GIS Map:** Real-time spatial tracking of cameras, vehicle detections, and traffic events using Leaflet.
- **Hotlist & Blacklist Alerts:** Real-time flagging of stolen, wanted, or suspicious vehicles with instant notification.
- **Urban Traffic Analytics:** Comprehensive statistics on traffic density, peak-hour flows, camera health, and violation trends.
- **Role-Based Access Control (RBAC):** Multi-tier access for Super Admins, Traffic Officers, Control Room operators, and Analysts.

---

## Tech Stack

- **Frontend:** React 18, Vite 5, React Router v6, Leaflet / React-Leaflet, Lucide Icons, Axios, Vanilla CSS
- **Backend:** Python 3.9+, FastAPI, SQLAlchemy 2.0 ORM, Pydantic v2, Uvicorn (ASGI)
- **Database:** SQLite (embedded `traffic_ai.db` for instant zero-dependency local run) / PostgreSQL (Supabase / PostGIS for cloud/production)
- **AI & Computer Vision:** Ultralytics YOLOv8 (`yolov8n.pt` / `yolov8m.pt`), PaddleOCR, OpenCV (FFmpeg RTSP streaming), Pillow, NumPy
- **Streaming Protocols:** WebRTC (WHEP), HLS, RTSP TCP transport, and live HTTP snapshot streaming
- **Authentication:** JWT (JSON Web Tokens) with 24-hour expiration, bcrypt password hashing

---

## Quick Start (Native Execution)

The project runs directly using Python and Node.js on your local system.

### Prerequisites

- **Python 3.9+** (Tested on Python 3.10 - 3.12)
- **Node.js 18+** & npm
- Git

---

### Step-by-Step Local Setup

#### 1. Clone & Navigate
```bash
git clone <repo-url>
cd "AI Traffic Engine"
```

#### 2. Start the Backend (FastAPI)
```bash
cd backend

# Create and activate virtual environment (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# (On macOS/Linux: source venv/bin/activate)

# Install dependencies
pip install -r requirements.txt

# Run database seed (creates default admin & demo accounts)
python seed_admin.py
python seed_demo_users.py

# Start the backend server
python run.py
```
> The backend server will start at **http://localhost:8000**  
> Interactive API Docs (Swagger UI): **http://localhost:8000/docs**

#### 3. Start the Frontend (React + Vite)
In a **separate terminal window**:
```bash
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```
> The frontend application will start at **http://localhost:5173**

---

## Default Demo Credentials

Pre-configured accounts are available for testing role-based access:

| Role | Officer ID / Username | Password | Access Level |
|---|---|---|---|
| **Super Admin** | `superadmin` | `admin123` | Full system control, user management, audit logs |
| **Traffic Officer** | `officer` | `officer123` | Vehicle searches, manual flagging, tracking |
| **Control Room** | `control` | `control123` | Live camera wall, real-time alerts, stream controls |
| **Analyst** | `analyst` | `analyst123` | Traffic analytics, charts, detection statistics |

---

## Project Structure

```
AI-Traffic-Engine/
├── backend/                       # FastAPI Backend Application
│   ├── app/
│   │   ├── main.py               # FastAPI entry point & middleware
│   │   ├── database.py           # SQLAlchemy session & SQLite/PostgreSQL engine
│   │   ├── models/               # Database ORM models (Users, Cameras, Detections, etc.)
│   │   ├── schemas/              # Pydantic validation schemas
│   │   ├── routers/              # API endpoints (Auth, Cameras, Search, Alerts, etc.)
│   │   ├── ai/                   # YOLOv8 vehicle detection & PaddleOCR recognition
│   │   ├── tracking/             # Trajectory reconstruction logic
│   │   └── core/                 # Security (JWT, bcrypt), config, logger
│   ├── snapshots/                # Cached live camera frame snapshots
│   ├── workers/                  # Live camera processing worker
│   ├── requirements.txt          # Python dependencies
│   ├── run.py                    # Backend development server runner
│   ├── seed_admin.py             # Script to initialize admin user
│   ├── seed_demo_users.py        # Script to seed role-based demo accounts
│   ├── seed_real_cameras.py      # Seed script for live RTSP / HLS traffic cameras
│   └── traffic_ai.db             # Local SQLite database file
│
├── frontend/                      # React 18 + Vite Application
│   ├── src/
│   │   ├── pages/                # Complete UI Dashboard Pages
│   │   │   ├── Login.jsx         # Authentication portal
│   │   │   ├── Dashboard.jsx     # High-level operational metrics & summaries
│   │   │   ├── CameraWall.jsx    # Live multi-stream camera grid (WebRTC / HLS / Snapshots)
│   │   │   ├── FindVehicle.jsx   # ANPR license plate search & history
│   │   │   ├── TrackVehicle.jsx  # Cross-camera trajectory visualizer
│   │   │   ├── LiveMap.jsx       # Interactive GIS Leaflet map
│   │   │   ├── Analytics.jsx     # Traffic flow & violation analytics
│   │   │   ├── Alerts.jsx        # Real-time alert list & status management
│   │   │   └── Blacklist.jsx     # Hotlist vehicle database management
│   │   ├── components/           # Reusable UI components (WebRTCPlayer, HlsPlayer, etc.)
│   │   ├── layouts/              # App layout with collapsible sidebar & navigation
│   │   ├── services/             # Axios API client & interceptors
│   │   ├── App.jsx               # Route definitions & ProtectedRoute wrapper
│   │   └── main.jsx              # React DOM entry point
│   ├── package.json              # Node dependencies & scripts
│   └── vite.config.js            # Vite build configuration
│
├── database/                      # SQL schemas and migrations
├── docs/                          # Requirements (PRD, TRD)
├── test_api.py                    # Automated test suite (validates 16+ API endpoints)
├── QUICKSTART.md                  # Quick setup and usage guide
├── CHECKLIST.md                   # Detailed implementation status matrix
├── IMPLEMENTATION_STATUS.md       # Comprehensive architecture and technical report
├── PROJECT_SUMMARY.md             # Project summary and deliverable overview
└── README.md                      # This document
```

---

## Key Features & Completed Pages

| Page / Feature | Route | Description |
|---|---|---|
| **Dashboard** | `/` | Operational KPI metrics, active camera count, 24h detection stats, alert activity, recent events. |
| **Live Camera Wall** | `/cameras` | Responsive multi-camera grid supporting WebRTC (WHEP), HLS, and live auto-refresh snapshots with stream diagnostics. |
| **Find Vehicle** | `/find-vehicle` | ANPR search by license plate, detection gallery, timestamp filtering, speed estimation, and manual flagging. |
| **Track Vehicle** | `/track` | Cross-camera journey reconstruction showing chrono-spatial path across the city. |
| **Live GIS Map** | `/map` | Interactive Leaflet map plotting all city cameras, their live status, and recent spatial alerts. |
| **Traffic Analytics** | `/analytics` | Interactive charts showing hourly traffic volume, vehicle type breakdown, camera hotspots, and system speed stats. |
| **Alerts & Incidents** | `/alerts` | Real-time security alerts with severity filtering, violation details, and status update workflows (New, Acknowledged, Resolved). |
| **Blacklist Management** | `/blacklist` | Hotlist management for flagged plates, vehicle descriptions, violation reasons, and automated matching. |

---

## API Documentation

Once the backend is running, access interactive OpenAPI documentation at:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)

---

## Automated Testing

Run the built-in API test suite to verify all backend routers, authentication, and database endpoints:

```bash
python test_api.py
```

---

## Configuration

Environment variables can be configured in `backend/.env` (refer to `.env.example`):
- `DATABASE_URL`: Defaults to `sqlite:///./traffic_ai.db` for local zero-setup execution, or PostgreSQL URL (e.g., Supabase) for production.
- `SECRET_KEY`: Cryptographic key for signing JWT tokens.
- `CORS_ORIGINS`: Allowed origins (default includes `http://localhost:5173`).
- `YOLO_MODEL`: YOLO weights to use (`yolov8n` or `yolov8m`).
- `STREAM_EMAIL` / `STREAM_PASSWORD` / `STREAM_HOST`: Sentinel camera feed access credentials.

---

## Contributors

- **Mohammed Wajahath Ullah Shareef**
- **Omar Farooq**
- **Team Coding Impasta**
