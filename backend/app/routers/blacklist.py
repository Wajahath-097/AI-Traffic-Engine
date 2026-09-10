from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime
import uuid

from app.database import get_db
from app.models.models import BlacklistEntry, User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/blacklist", tags=["blacklist"])

class BlacklistCreate(BaseModel):
    plate_number: str
    reason: str
    severity: str = "high"

class BlacklistResponse(BaseModel):
    id: uuid.UUID
    plate_number: str
    reason: str
    severity: str
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[BlacklistResponse])
def get_blacklist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.models import VehicleDetection
    entries = db.query(BlacklistEntry).order_by(BlacklistEntry.created_at.desc()).all()
    
    result = []
    for entry in entries:
        latest_det = db.query(VehicleDetection).filter(VehicleDetection.plate_number == entry.plate_number).order_by(VehicleDetection.detected_at.desc()).first()
        
        entry_dict = {
            "id": entry.id,
            "plate_number": entry.plate_number,
            "reason": entry.reason,
            "severity": entry.severity,
            "created_at": entry.created_at,
            "expires_at": entry.expires_at,
            "vehicle_class": latest_det.vehicle_class.capitalize() if latest_det and latest_det.vehicle_class else "Unknown",
            "vehicle_color": latest_det.vehicle_color.capitalize() if latest_det and latest_det.vehicle_color else "Unknown"
        }
        result.append(entry_dict)
        
    return result

@router.post("", response_model=BlacklistResponse)
def add_blacklist(entry: BlacklistCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(BlacklistEntry).filter(BlacklistEntry.plate_number == entry.plate_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Plate is already blacklisted")
        
    db_entry = BlacklistEntry(
        plate_number=entry.plate_number.replace(" ", "").upper(),
        reason=entry.reason,
        severity=entry.severity,
        created_by=current_user.id
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.delete("/{entry_id}")
def delete_blacklist(entry_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = db.query(BlacklistEntry).filter(BlacklistEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
        
    db.delete(entry)
    db.commit()
    return {"message": "Entry removed successfully"}
