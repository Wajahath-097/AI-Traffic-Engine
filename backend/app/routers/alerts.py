"""
Alert management and incident routes
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.models import Alert, VehicleDetection, Camera, AuditLog, BlacklistEntry
from app.schemas.schemas import AlertCreate, AlertResponse, AlertUpdate
from app.core.dependencies import get_current_control_room, get_current_super_admin, get_current_user
from app.models.models import User
from typing import List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    severity: str = Query(None, regex="^(critical|high|medium|low)$"),
    status_filter: str = Query(None, regex="^(open|investigating|resolved|dismissed)$"),
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_control_room),
    db: Session = Depends(get_db)
):
    """
    Get list of recent alerts
    """
    query = db.query(Alert).order_by(desc(Alert.created_at))
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    if status_filter:
        query = query.filter(Alert.status == status_filter)
    
    alerts = query.limit(limit).all()
    
    return [AlertResponse.from_orm(a) for a in alerts]


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: User = Depends(get_current_control_room),
    db: Session = Depends(get_db)
):
    """
    Get alert details with evidence
    """
    try:
        from uuid import UUID
        alert_uuid = UUID(alert_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert ID format"
        )
    
    alert = db.query(Alert).filter(Alert.id == alert_uuid).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Log access
    audit_log = AuditLog(
        user_id=current_user.id,
        action="view_alert",
        resource_type="alert",
        resource_id=alert_id
    )
    db.add(audit_log)
    db.commit()
    
    return AlertResponse.from_orm(alert)


@router.put("/{alert_id}/status", response_model=AlertResponse)
async def update_alert_status(
    alert_id: str,
    new_status: str = Query(..., regex="^(open|investigating|resolved|dismissed)$"),
    current_user: User = Depends(get_current_control_room),
    db: Session = Depends(get_db)
):
    """
    Update alert status (investigating, resolved, dismissed)
    """
    try:
        from uuid import UUID
        alert_uuid = UUID(alert_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert ID format"
        )
    
    alert = db.query(Alert).filter(Alert.id == alert_uuid).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    old_status = alert.status
    alert.status = new_status
    alert.updated_at = datetime.utcnow()
    
    if new_status == "resolved":
        alert.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(alert)
    
    # Log status change
    audit_log = AuditLog(
        user_id=current_user.id,
        action="update_alert_status",
        resource_type="alert",
        resource_id=alert_id,
        details={"old_status": old_status, "new_status": new_status}
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"Alert status updated by {current_user.officer_id}: {alert_id} - {old_status} -> {new_status}")
    
    return AlertResponse.from_orm(alert)


@router.post("/{alert_id}/investigate", response_model=AlertResponse)
async def investigate_alert(
    alert_id: str,
    notes: str = Query(None),
    current_user: User = Depends(get_current_control_room),
    db: Session = Depends(get_db)
):
    """
    Mark alert as under investigation
    """
    try:
        from uuid import UUID
        alert_uuid = UUID(alert_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert ID format"
        )
    
    alert = db.query(Alert).filter(Alert.id == alert_uuid).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    alert.status = "investigating"
    alert.assigned_to = current_user.id
    alert.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(alert)
    
    # Log investigation
    audit_log = AuditLog(
        user_id=current_user.id,
        action="investigate_alert",
        resource_type="alert",
        resource_id=alert_id,
        details={"notes": notes}
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"Alert investigation started by {current_user.officer_id}: {alert_id}")
    
    return AlertResponse.from_orm(alert)


@router.get("/stats/summary")
async def get_alert_summary(
    current_user: User = Depends(get_current_control_room),
    db: Session = Depends(get_db)
):
    """
    Get alert statistics and summary
    """
    all_alerts = db.query(Alert).all()
    
    summary = {
        "total_alerts": len(all_alerts),
        "by_severity": {
            "critical": len([a for a in all_alerts if a.severity == "critical"]),
            "high": len([a for a in all_alerts if a.severity == "high"]),
            "medium": len([a for a in all_alerts if a.severity == "medium"]),
            "low": len([a for a in all_alerts if a.severity == "low"])
        },
        "by_status": {
            "open": len([a for a in all_alerts if a.status == "open"]),
            "investigating": len([a for a in all_alerts if a.status == "investigating"]),
            "resolved": len([a for a in all_alerts if a.status == "resolved"]),
            "dismissed": len([a for a in all_alerts if a.status == "dismissed"])
        },
        "by_type": {
            "blacklist_match": len([a for a in all_alerts if a.alert_type == "blacklist_match"]),
            "repeated_hits": len([a for a in all_alerts if a.alert_type == "repeated_hits"]),
            "low_confidence": len([a for a in all_alerts if a.alert_type == "low_confidence"]),
            "offline": len([a for a in all_alerts if a.alert_type == "offline"]),
            "anomaly": len([a for a in all_alerts if a.alert_type == "anomaly"]),
            "manual_flag": len([a for a in all_alerts if a.alert_type == "manual_flag"])
        }
    }
    
    return summary


@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new alert (typically from alert engine)
    """
    # Create alert
    new_alert = Alert(
        severity=alert_data.severity,
        alert_type=alert_data.alert_type,
        plate_number=alert_data.plate_number,
        camera_id=alert_data.camera_id,
        detection_id=alert_data.detection_id,
        message=alert_data.message,
        evidence_ref=alert_data.evidence_ref,
        status="open"
    )
    
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    
    logger.info(f"Alert created: {new_alert.alert_type} - {new_alert.severity}")
    
    return AlertResponse.from_orm(new_alert)
