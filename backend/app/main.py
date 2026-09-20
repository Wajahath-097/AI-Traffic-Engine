"""
Traffic AI Engine - FastAPI Application Entry Point
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Optional
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import setup_logging
from app.database import engine, SessionLocal, get_db
from app.models.models import Base, Role
from app.routers import auth, cameras, detection, detections, search, trajectories, alerts, analytics, admin, blacklist

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting Traffic AI Engine...")
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
        
        # Initialize default roles
        db = SessionLocal()
        try:
            role_count = db.query(Role).count()
            if role_count == 0:
                default_roles = [
                    Role(name="Super Admin", description="Full system administration"),
                    Role(name="Traffic Officer", description="Assigned cameras + vehicle searches"),
                    Role(name="Control Room", description="Live feeds + alerts"),
                    Role(name="Analyst", description="Reports/statistics"),
                    Role(name="Auditor", description="Logs only")
                ]
                for role in default_roles:
                    db.add(role)
                db.commit()
                logger.info("Default roles initialized")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Traffic AI Engine...")


app = FastAPI(
    title="Traffic AI Engine API",
    description="City-Wide Multi-Camera ANPR and Traffic Analytics",
    version="0.1.0",
    lifespan=lifespan
)

# Middleware Configuration
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*"]
)

# API Routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(cameras.router, prefix="/api/cameras", tags=["Cameras"])
app.include_router(detection.router, prefix="/api/detection", tags=["Detection"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(trajectories.router, prefix="/api/trajectories", tags=["Trajectories"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(admin.router, prefix="/api/admin", tags=["Administration"])
app.include_router(blacklist.router)
app.include_router(detections.router)

import os
media_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "media")
if os.path.exists(media_path):
    app.mount("/api/media", StaticFiles(directory=media_path), name="media")


@app.get("/api/ingest")
def sentinel_ingest_catalogue(db: Session = Depends(get_db)):
    """
    Catalogue endpoint compliant with Sentinel Sandbox specification:
    Returns camera list, status, codec, and all three protocol endpoints (RTSP, WebRTC/WHEP, HLS).
    """
    from app.routers.cameras import get_ingest_catalogue
    return get_ingest_catalogue(db=db)




@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "Traffic AI Engine API",
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """
    API documentation redirect
    """
    return {
        "message": "Traffic AI Engine API",
        "docs": "/docs",
        "health": "/health",
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=settings.FASTAPI_ENV == "development",
        workers=1 if settings.FASTAPI_ENV == "development" else settings.FASTAPI_WORKERS
    )
