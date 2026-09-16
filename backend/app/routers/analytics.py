"""
Analytics and reporting routes
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.models.models import VehicleDetection, Camera, CameraHealthEvent, Alert, AuditLog, Journey
from app.core.dependencies import get_current_analyst, get_current_user
from app.models.models import User
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_analytics(
    date_range: str = Query("24h", regex="^(24h|7d|30d|90d)$"),
    current_user: User = Depends(get_current_analyst),
    db: Session = Depends(get_db)
):
    """
    Get dashboard summary analytics
    """
    # Parse date range
    hours_map = {"24h": 24, "7d": 168, "30d": 720, "90d": 2160}
    hours = hours_map.get(date_range, 24)
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Total detections overall (AI processes offline video files, not real-time)
    total_detections = db.query(func.count(VehicleDetection.id))\
        .filter(VehicleDetection.created_at >= cutoff_time)\
        .scalar() or 0
    
    # Detections by hour
    dialect = db.bind.dialect.name
    if dialect == "sqlite":
        hour_expr = func.strftime("%Y-%m-%d %H:00", VehicleDetection.created_at)
    else:
        hour_expr = func.to_char(VehicleDetection.created_at, "YYYY-MM-DD HH:00")

    detections_by_hour = db.query(
        hour_expr.label("hour"),
        func.count(VehicleDetection.id).label("count")
    ).filter(VehicleDetection.created_at >= cutoff_time)\
    .group_by("hour")\
    .order_by("hour")\
    .all()
    
    # Top cameras by detection count
    top_cameras_data = db.query(
        Camera.camera_id,
        Camera.name,
        func.count(VehicleDetection.id).label("detection_count")
    ).outerjoin(VehicleDetection)\
    .filter(VehicleDetection.created_at >= cutoff_time)\
    .group_by(Camera.id, Camera.camera_id, Camera.name)\
    .order_by(desc("detection_count"))\
    .limit(10)\
    .all()
    
    top_cameras = [
        {
            "camera_id": cam[0],
            "camera_name": cam[1],
            "detection_count": cam[2] or 0
        }
        for cam in top_cameras_data
    ]
    
    # Camera uptime
    camera_uptime = {}
    cameras = db.query(Camera).all()
    for cam in cameras:
        total_health_events = db.query(func.count(CameraHealthEvent.id))\
            .filter(CameraHealthEvent.camera_id == cam.id,
                   CameraHealthEvent.recorded_at >= cutoff_time)\
            .scalar() or 0
        
        online_events = db.query(func.count(CameraHealthEvent.id))\
            .filter(CameraHealthEvent.camera_id == cam.id,
                   CameraHealthEvent.status == "online",
                   CameraHealthEvent.recorded_at >= cutoff_time)\
            .scalar() or 0
        
        uptime_pct = (online_events / total_health_events * 100) if total_health_events > 0 else 0
        camera_uptime[cam.camera_id] = {
            "uptime_percentage": round(uptime_pct, 2),
            "status": cam.status
        }
    
    # Alert summary
    alert_summary = {
        "total_alerts": db.query(func.count(Alert.id))\
            .filter(Alert.created_at >= cutoff_time)\
            .scalar() or 0,
        "by_severity": {
            "critical": db.query(func.count(Alert.id))\
                .filter(Alert.severity == "critical", Alert.created_at >= cutoff_time)\
                .scalar() or 0,
            "high": db.query(func.count(Alert.id))\
                .filter(Alert.severity == "high", Alert.created_at >= cutoff_time)\
                .scalar() or 0,
            "medium": db.query(func.count(Alert.id))\
                .filter(Alert.severity == "medium", Alert.created_at >= cutoff_time)\
                .scalar() or 0,
            "low": db.query(func.count(Alert.id))\
                .filter(Alert.severity == "low", Alert.created_at >= cutoff_time)\
                .scalar() or 0
        },
        "by_status": {
            "open": db.query(func.count(Alert.id))\
                .filter(Alert.status == "open", Alert.created_at >= cutoff_time)\
                .scalar() or 0,
            "investigating": db.query(func.count(Alert.id))\
                .filter(Alert.status == "investigating", Alert.created_at >= cutoff_time)\
                .scalar() or 0,
            "resolved": db.query(func.count(Alert.id))\
                .filter(Alert.status == "resolved", Alert.created_at >= cutoff_time)\
                .scalar() or 0
        }
    }
    
    # Get long-term totals
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    
    total_24h = db.query(func.count(VehicleDetection.id)).filter(VehicleDetection.created_at >= twenty_four_hours_ago).scalar() or 0
    total_7d = db.query(func.count(VehicleDetection.id)).filter(VehicleDetection.created_at >= seven_days_ago).scalar() or 0
    total_30d = db.query(func.count(VehicleDetection.id)).filter(VehicleDetection.created_at >= thirty_days_ago).scalar() or 0
    total_5m = db.query(func.count(VehicleDetection.id)).filter(VehicleDetection.created_at >= five_minutes_ago).scalar() or 0

    return {
        "total_detections": total_detections,
        "total_5m": total_5m,
        "total_24h": total_24h,
        "total_7d": total_7d,
        "total_30d": total_30d,
        "date_range": date_range,
        "detections_by_hour": [
            {"hour": h[0], "count": h[1]}
            for h in detections_by_hour
        ],
        "top_cameras": top_cameras,
        "camera_uptime": camera_uptime,
        "alert_summary": alert_summary
    }


@router.get("/detections")
async def get_detection_analytics(
    camera_id: str = Query(None),
    date_range: str = Query("24h", regex="^(24h|7d|30d|90d)$"),
    current_user: User = Depends(get_current_analyst),
    db: Session = Depends(get_db)
):
    """
    Get detection statistics and trends
    """
    hours_map = {"24h": 24, "7d": 168, "30d": 720, "90d": 2160}
    hours = hours_map.get(date_range, 24)
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    query = db.query(VehicleDetection)\
        .filter(VehicleDetection.created_at >= cutoff_time)
    
    if camera_id:
        camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        if camera:
            query = query.filter(VehicleDetection.camera_id == camera.id)
    
    detections = query.all()
    
    total = len(detections)
    with_plates = len([d for d in detections if d.plate_number])
    high_confidence = len([d for d in detections if d.plate_confidence and d.plate_confidence >= 0.8])
    
    return {
        "total_detections": total,
        "with_plates": with_plates,
        "high_confidence_detections": high_confidence,
        "vehicle_classes": {
            "car": len([d for d in detections if d.vehicle_class == "car"]),
            "truck": len([d for d in detections if d.vehicle_class == "truck"]),
            "bike": len([d for d in detections if d.vehicle_class == "bike"]),
            "other": len([d for d in detections if d.vehicle_class not in ["car", "truck", "bike"]])
        }
    }


@router.get("/ocr-accuracy")
async def get_ocr_accuracy(
    camera_id: str = Query(None),
    current_user: User = Depends(get_current_analyst),
    db: Session = Depends(get_db)
):
    """
    Get OCR accuracy and confidence statistics
    """
    query = db.query(VehicleDetection)\
        .filter(VehicleDetection.plate_confidence != None)
    
    if camera_id:
        camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        if camera:
            query = query.filter(VehicleDetection.camera_id == camera.id)
    
    detections = query.all()
    
    if not detections:
        return {
            "average_confidence": 0.0,
            "total_recognitions": 0,
            "confidence_distribution": {}
        }
    
    confidences = [d.plate_confidence for d in detections]
    
    return {
        "average_confidence": sum(confidences) / len(confidences),
        "total_recognitions": len(confidences),
        "high_confidence": len([c for c in confidences if c >= 0.8]),
        "medium_confidence": len([c for c in confidences if 0.5 <= c < 0.8]),
        "low_confidence": len([c for c in confidences if c < 0.5]),
        "confidence_distribution": {
            "0.0-0.3": len([c for c in confidences if c < 0.3]),
            "0.3-0.5": len([c for c in confidences if 0.3 <= c < 0.5]),
            "0.5-0.7": len([c for c in confidences if 0.5 <= c < 0.7]),
            "0.7-0.9": len([c for c in confidences if 0.7 <= c < 0.9]),
            "0.9-1.0": len([c for c in confidences if c >= 0.9])
        }
    }


@router.get("/traffic-patterns")
async def get_traffic_patterns(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user: User = Depends(get_current_analyst),
    db: Session = Depends(get_db)
):
    """
    Get traffic flow patterns and congestion indicators
    """
    detections = db.query(VehicleDetection)\
        .filter(VehicleDetection.detected_at >= start_date,
               VehicleDetection.detected_at <= end_date)\
        .all()
    
    # Group by hour
    patterns = {}
    for detection in detections:
        hour = detection.detected_at.strftime("%H:00")
        if hour not in patterns:
            patterns[hour] = 0
        patterns[hour] += 1
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "patterns": patterns,
        "peak_hour": max(patterns, key=patterns.get) if patterns else None
    }


@router.get("/camera-performance")
async def get_camera_performance(
    current_user: User = Depends(get_current_analyst),
    db: Session = Depends(get_db)
):
    """
    Get performance metrics for all cameras
    """
    cameras = db.query(Camera).all()
    
    performance = {}
    for camera in cameras:
        detection_count = db.query(func.count(VehicleDetection.id))\
            .filter(VehicleDetection.camera_id == camera.id)\
            .scalar() or 0
        
        health_events = db.query(CameraHealthEvent)\
            .filter(CameraHealthEvent.camera_id == camera.id)\
            .order_by(desc(CameraHealthEvent.recorded_at))\
            .limit(100)\
            .all()
        
        avg_latency = 0
        if health_events:
            latencies = [e.latency_ms for e in health_events if e.latency_ms]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        performance[camera.camera_id] = {
            "name": camera.name,
            "status": camera.status,
            "detection_count": detection_count,
            "avg_latency_ms": round(avg_latency, 2),
            "last_heartbeat": camera.last_heartbeat.isoformat() if camera.last_heartbeat else None
        }
    
    return {"cameras": performance}

@router.get("/heatmap")
async def get_traffic_heatmap(
    date_range: str = Query("24h", regex="^(24h|7d|30d|90d)$"),
    current_user: User = Depends(get_current_analyst),
    db: Session = Depends(get_db)
):
    """
    Get heatmap data for traffic congestion bottlenecks
    """
    hours_map = {"24h": 24, "7d": 168, "30d": 720, "90d": 2160}
    hours = hours_map.get(date_range, 24)
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    heatmap_data = db.query(
        Camera.latitude,
        Camera.longitude,
        func.count(VehicleDetection.id).label("intensity")
    ).join(VehicleDetection).filter(
        Camera.latitude.isnot(None),
        Camera.longitude.isnot(None)
    ).group_by(Camera.id, Camera.latitude, Camera.longitude).all()
    
    return [
        {"lat": float(lat), "lng": float(lng), "intensity": intensity}
        for lat, lng, intensity in heatmap_data
    ]

@router.get("/origin-destination")
async def get_origin_destination_patterns(
    date_range: str = Query("24h", regex="^(24h|7d|30d|90d)$"),
    current_user: User = Depends(get_current_analyst),
    db: Session = Depends(get_db)
):
    """
    Get macro origin-destination traffic flow patterns
    """
    hours_map = {"24h": 24, "7d": 168, "30d": 720, "90d": 2160}
    hours = hours_map.get(date_range, 24)
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    od_patterns = db.query(
        Journey.start_camera_id,
        Journey.end_camera_id,
        func.count(Journey.id).label("count")
    ).filter(
        Journey.created_at >= cutoff_time,
        Journey.start_camera_id != Journey.end_camera_id
    ).group_by(Journey.start_camera_id, Journey.end_camera_id).order_by(desc("count")).limit(20).all()
    
    result = []
    for start_id, end_id, count in od_patterns:
        start_cam = db.query(Camera).filter(Camera.id == start_id).first()
        end_cam = db.query(Camera).filter(Camera.id == end_id).first()
        if start_cam and end_cam:
            result.append({
                "origin": start_cam.name,
                "destination": end_cam.name,
                "count": count
            })
            
    return {"patterns": result}

