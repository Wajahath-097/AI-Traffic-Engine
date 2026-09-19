# Traffic AI Engine

City-Wide Multi-Camera ANPR, Trajectory Tracking & Urban Traffic Analytics

**Team:** Coding Impasta
**SIH Problem Statement ID:** 26127  
**Theme:** Smart Automation

## Project Overview

Traffic AI Engine is a centralized platform that unifies CCTV/ANPR camera feeds into a single operational intelligence system. The system provides live multi-camera ingestion, vehicle and number-plate detection, OCR, cross-camera trajectory reconstruction, GIS visualization, and comprehensive traffic analytics.

## Tech Stack

- **Frontend:** React + Vite, Leaflet for GIS
- **Backend:** Python + FastAPI, SQLAlchemy ORM
- **Database:** PostgreSQL with PostGIS
- **Event Bus:** Apache Kafka (for scalability)
- **AI/ML:** YOLOv8, PaddleOCR, OpenCV
- **Media:** MediaMTX for RTSP streaming
- **Containerization:** Docker & Docker Compose
- **Authentication:** JWT/Session-based
- **Reverse Proxy:** Nginx

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.9+
- PostgreSQL 13+

### Development Setup

```bash
# Clone and navigate
cd "ai trafic engine"

# Install dependencies
cd frontend && npm install
cd ../backend && pip install -r requirements.txt

# Start services
docker-compose up

# Run development servers
# Frontend: cd frontend && npm run dev
# Backend: cd backend && .\venv\Scripts\Activate.ps1 && python run.py
```

### Default Credentials
- **Super Admin:** `superadmin` / `admin123`
- **Traffic Officer:** `officer` / `officer123`
- **Control Room:** `control` / `control123`
- **Analyst:** `analyst` / `analyst123`

## Project Structure

```
traffic-ai-engine/
├── frontend/          # React + Vite dashboard
├── backend/           # FastAPI services
├── workers/           # AI processing workers
├── media/             # MediaMTX stream gateway
├── database/          # Schema & migrations
├── docker/            # Docker configurations
├── scripts/           # Utility scripts
└── docs/              # Requirements & documentation
```

## Key Features

- ✅ Multi-camera live stream ingestion (10 cameras in MVP)
- ✅ Vehicle & plate detection using YOLOv8
- ✅ OCR with confidence scoring (PaddleOCR)
- ✅ Cross-camera trajectory reconstruction
- ✅ GIS-based visualization
- ✅ Blacklist & suspicious vehicle alerts
- ✅ Vehicle search & analytics
- ✅ Role-based access control
- ✅ Audit logging
- ✅ Real-time event streaming

## Documentation

- [PRD - Product Requirements](docs/PRD_Traffic_AI_Engine.md)
- [TRD - Technical Requirements](docs/TRD_Traffic_AI_Engine.md)

## Architecture

See [TRD Section 2](docs/TRD_Traffic_AI_Engine.md#2-high-level-architecture) for detailed architecture diagram and component descriptions.

## Development Workflow

1. **Backend Development:** FastAPI routes, database models, business logic
2. **Frontend Development:** React components, pages, API integration
3. **AI Pipeline:** Frame processing, detection, OCR, trajectory tracking
4. **Testing & Validation:** Unit tests, integration tests, end-to-end testing

## Configuration

All configuration is managed through `.env` files (see `.env.example`).

## Deployment

### Local Development
```bash
docker-compose -f docker-compose.yml up
```

### LAN / Demonstration
See deployment guide in docs for binding to LAN interface.

### Cloud
Refer to cloud deployment section in documentation.

## Security

- HTTPS in production
- Secure password hashing
- JWT token-based authentication
- Role-based access control (RBAC)
- Audit logging for sensitive operations
- Environment-based secrets management

## License

Internal project for SIH 2026 submission.

## Contributors

Mohammed Wajahath Ullah Shareef
Omar Farooq
