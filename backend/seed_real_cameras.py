import random
from datetime import datetime
import os
import sys

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.models import Camera, VehicleDetection, Alert, Journey, JourneyEvent, BlacklistEntry, User, Role, CameraHealthEvent, AuditLog

def seed_real_cameras():
    db = SessionLocal()
    try:
        # Clear existing
        print("Clearing all data to remove fake/mock data...")
        db.query(JourneyEvent).delete()
        db.query(Journey).delete()
        db.query(Alert).delete()
        db.query(VehicleDetection).delete()
        db.query(BlacklistEntry).delete()
        db.query(CameraHealthEvent).delete()
        db.query(Camera).delete()
        db.query(AuditLog).delete()
        db.query(User).delete()
        db.query(Role).delete()
        db.commit()

        print("Creating User and Roles...")
        role = Role(name="officer", description="Traffic Officer")
        db.add(role)
        db.commit()
        
        import bcrypt
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(b"password123", salt).decode('utf-8')
        
        # Create test officer
        user = User(
            officer_id="OFFICER-001",
            password_hash=hashed_pw,
            name="Test Officer",
            role_id=role.id,
            is_active=True
        )
        db.add(user)
        db.commit()

        print("Creating actual cameras (CAM-001, CAM-002, CAM-003)...")
        base_lat, base_lng = 17.3850, 78.4867 # Hyderabad, India
        
        cameras = [
            ("CAM-001", "Jubilee Hills Checkpost", base_lat + 0.005, base_lng - 0.005),
            ("CAM-002", "Banjara Hills Rd No. 12", base_lat + 0.010, base_lng + 0.005),
            ("CAM-003", "Gachibowli ORR Junction", base_lat - 0.008, base_lng + 0.002),
        ]
        
        for cam_id, name, lat, lng in cameras:
            cam = Camera(
                camera_id=cam_id,
                name=name,
                location=f"Zone {cam_id[-1]}",
                latitude=lat,
                longitude=lng,
                status="online",
                enabled=True,
                last_heartbeat=datetime.utcnow()
            )
            db.add(cam)
        
        db.commit()
        print("Done setting up real cameras!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_real_cameras()
