# Quick Start Guide - Traffic AI Engine

## Prerequisites

- Python 3.9+ (for local development)
- Node.js 18+ (for local frontend development)
- PostgreSQL 13+ (or SQLite)

## Setup

## Quick Start (The Easy Way)

### Step 1: Start the Python Backend
Open a terminal, go to the backend folder, and run the server:
```bash
cd backend
.\venv\Scripts\Activate.ps1
python run.py
```
*(The backend will run on http://localhost:8000)*

### Step 2: Start the Node.js Frontend
Open a **new** terminal, go to the frontend folder, and start the UI:
```bash
cd frontend
npm run dev
```
*(The frontend will run on http://localhost:5173)*

### Step 3: Access the App!
Click here to open the application: [http://localhost:5173/login](http://localhost:5173/login)

**Default Demo Credentials:**
- Super Admin: `superadmin` / `admin123`
- Traffic Officer: `officer` / `officer123`
- Control Room: `control` / `control123`
- Analyst: `analyst` / `analyst123`

---
*Note: The frontend is entirely powered by Node.js, and the backend is powered by Python/FastAPI. All Node.js dependencies are contained cleanly within the `frontend/node_modules` folder.*



## Project Structure

```
traffic-ai-engine/
├── frontend/                 # React + Vite dashboard
│   ├── src/
│   │   ├── components/      # Reusable React components
│   │   ├── pages/           # Page components
│   │   ├── layouts/         # Layout components
│   │   ├── services/        # API services
│   │   ├── hooks/           # Custom React hooks
│   │   ├── context/         # React context providers
│   │   ├── assets/          # Images, fonts, etc.
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── database.py      # Database configuration
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── routers/         # API route handlers
│   │   ├── services/        # Business logic
│   │   ├── ai/              # AI/ML processing
│   │   ├── tracking/        # Trajectory tracking
│   │   ├── alerts/          # Alert logic
│   │   └── core/            # Core utilities (config, logger, etc.)
│   ├── requirements.txt
│   └── run.py               # Development entry point
│
├── workers/                  # Background workers
│   ├── camera_worker/       # Camera stream processing
│   ├── detection_worker/    # Vehicle detection
│   ├── ocr_worker/          # Plate recognition
│   └── tracking_worker/     # Trajectory reconstruction
│
├── database/                 # Database utilities
│   ├── migrations/          # SQL migration scripts
│   └── seed/                # Database seed data
│
├── docs/                     # Documentation
│   ├── PRD_Traffic_AI_Engine.md
│   └── TRD_Traffic_AI_Engine.md
│
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # Project overview
```

## Key Features to Implement

### Priority 1: Foundation
- [ ] User authentication & authorization
- [ ] Camera management CRUD
- [ ] Database models for detections and events
- [ ] Basic REST API structure

### Priority 2: Core Functionality
- [ ] Live camera stream ingestion (RTSP)
- [ ] Vehicle detection (YOLOv8)
- [ ] Plate recognition (PaddleOCR)
- [ ] Detection persistence

### Priority 3: Intelligence
- [ ] Trajectory reconstruction
- [ ] Cross-camera matching
- [ ] Alert engine
- [ ] Blacklist management

### Priority 4: UI & Analytics
- [ ] Frontend dashboard
- [ ] Live camera wall
- [ ] Vehicle search interface
- [ ] Analytics & reporting
- [ ] GIS visualization

## API Endpoints (Implemented Structure)

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `POST /api/auth/register` - Register user (admin)

### Cameras
- `GET /api/cameras/` - List cameras
- `GET /api/cameras/{camera_id}` - Get camera details
- `POST /api/cameras/` - Add camera (admin)
- `PUT /api/cameras/{camera_id}` - Update camera (admin)
- `DELETE /api/cameras/{camera_id}` - Delete camera (admin)
- `GET /api/cameras/{camera_id}/health` - Get camera health

### Detection & Search
- `GET /api/detection/detections` - Get detections
- `GET /api/search/vehicles` - Search vehicles by plate
- `GET /api/search/vehicles/{detection_id}/history` - Get vehicle history

### Trajectories
- `GET /api/trajectories/` - List trajectories
- `GET /api/trajectories/{trajectory_id}` - Get trajectory details
- `POST /api/trajectories/reconstruct` - Reconstruct trajectory

### Alerts
- `GET /api/alerts/` - List alerts
- `GET /api/alerts/{alert_id}` - Get alert details
- `PUT /api/alerts/{alert_id}/status` - Update alert status

### Analytics
- `GET /api/analytics/dashboard` - Dashboard metrics
- `GET /api/analytics/detections` - Detection analytics
- `GET /api/analytics/traffic-patterns` - Traffic patterns

### Administration
- `GET /api/admin/users` - List users (admin)
- `POST /api/admin/users` - Create user (admin)
- `GET /api/admin/audit-logs` - Audit logs (admin)
- `GET /api/admin/blacklist` - Blacklist (admin)
- `POST /api/admin/blacklist` - Add to blacklist (admin)

## Development Workflow

1. **Start with Backend Implementation**
   - Implement database models
   - Create authentication middleware
   - Build core API endpoints
   - Test with Postman/Insomnia

2. **Implement AI Pipeline**
   - Setup frame capture from cameras
   - Integrate YOLOv8 for detection
   - Implement PaddleOCR
   - Add confidence scoring & re-checking

3. **Build Frontend**
   - Create login page & auth flow
   - Implement dashboard
   - Build camera wall component
   - Add search interface

4. **Connect & Test**
   - Wire frontend to backend APIs
   - Test end-to-end workflows
   - Performance testing with 10 cameras
   - Load testing

## Configuration

### Environment Variables

See `.env.example` for all available settings:

```bash
# Important variables to configure:
DATABASE_URL=postgresql://user:password@localhost:5432/traffic_ai
SECRET_KEY=your-secure-key
FASTAPI_DEBUG=false  # Set to false in production
CORS_ORIGINS=["https://yourdomain.com"]
KAFKA_BROKER_URL=kafka:9092
```

## Running Tests

### Backend
```bash
cd backend
pytest tests/ -v
```

### Frontend
```bash
cd frontend
npm test
```

## Deployment

### Local Deployment
```bash
# Start backend in one terminal
cd backend
.\venv\Scripts\Activate.ps1
python run.py

# Start frontend in another terminal
cd frontend
npm run dev
```

### Accessing the Application

Once both servers are running, you can access the application using the following links:

- **Frontend Application (Login):** [http://localhost:5173/login](http://localhost:5173/login)
- **Backend API Base URL:** [http://localhost:8000](http://localhost:8000)
- **API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Documentation (ReDoc):** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Production Deployment
1. Use production database (managed PostgreSQL)
2. Set SECRET_KEY to secure random value
3. Disable DEBUG mode
4. Use HTTPS with valid certificates
5. Configure CORS for your domain
6. Setup Redis for caching
7. Use Nginx reverse proxy

## Troubleshooting

### Database Connection Issues
```bash
# Ensure PostgreSQL is running on your system
# Or ensure SQLite database file exists in backend folder
```

### Backend API Not Responding
```bash
# Check backend console output for errors

# Check if port 8000 is in use
netstat -an | grep 8000
```

### Frontend Build Issues
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

1. **Review and modify** the database schema if needed
2. **Implement authentication** with JWT tokens
3. **Setup camera management** interface
4. **Integrate RTSP stream** from real cameras or RTSP test server
5. **Implement vehicle detection** with YOLOv8
6. **Add OCR processing** with confidence scoring
7. **Build trajectory reconstruction** algorithm
8. **Create dashboard visualizations**

## Support & Documentation

- See `docs/PRD_Traffic_AI_Engine.md` for feature requirements
- See `docs/TRD_Traffic_AI_Engine.md` for technical architecture
- Check API documentation at `http://localhost:8000/docs` (Swagger UI)
- Review code comments for implementation notes

## Git Workflow

```bash
# Initial commit
git init
git add .
git commit -m "Initial Traffic AI Engine project scaffold"

# Feature branches
git checkout -b feature/authentication
# ... make changes ...
git commit -m "Implement JWT authentication"
git push origin feature/authentication

# Create pull request on GitHub for review
```

Good luck with your Traffic AI Engine implementation! 🚀
