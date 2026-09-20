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

        print("Creating actual cameras (CAM01 to CAM30)...")
        base_lat, base_lng = 23.0225, 72.5714 # Ahmedabad, Gujarat
        
        cameras = [
            ("CAM01", "Chiman bhai Bridge", base_lat + 0.01, base_lng + 0.01),
            ("CAM02", "Janpath", base_lat + 0.02, base_lng + 0.02),
            ("CAM03", "O.N.G.C. Office", base_lat + 0.03, base_lng + 0.03),
            ("CAM04", "Paldi Circle", base_lat + 0.04, base_lng + 0.04),
            ("CAM05", "Visat teen Rasta", base_lat + 0.05, base_lng + 0.05),
            ("CAM06", "Timbavadi gate Junagadh", base_lat - 0.01, base_lng - 0.01),
            ("CAM07", "hero showroom gir somnath", base_lat - 0.02, base_lng - 0.02),
            ("CAM08", "majewadi gate junagadh", base_lat - 0.03, base_lng - 0.03),
            ("CAM09", "new bypass near by circle junagadh 2", base_lat - 0.04, base_lng - 0.04),
            ("CAM10", "char chowk road 2 junagadh", base_lat - 0.05, base_lng - 0.05),
            ("CAM11", "dolatpara-junagadh", base_lat - 0.06, base_lng - 0.06),
            ("CAM12", "Tri Mandir Adalaj Tollnaka", base_lat + 0.06, base_lng + 0.06),
            ("CAM13", "CN Vidhyalaya", base_lat + 0.07, base_lng + 0.07),
            ("CAM14", "Delight RLVD", base_lat + 0.08, base_lng + 0.08),
            ("CAM15", "Suvidha park", base_lat + 0.09, base_lng + 0.09),
            ("CAM16", "Visat P2", base_lat + 0.10, base_lng + 0.10),
            ("CAM17", "Rajkot Bus Port CCTV", base_lat - 0.07, base_lng - 0.07),
            ("CAM18", "Rajkot CCTV", base_lat - 0.08, base_lng - 0.08),
            ("CAM19", "KHAPARIA GRAM PANCHAYAT , TALUKA GANDEVI, DISTRICT NAVSARI", base_lat - 0.09, base_lng - 0.09),
            ("CAM20", "Mohanpura", base_lat + 0.11, base_lng + 0.11),
            ("CAM21", "Patan Dethali Char Rasta", base_lat + 0.12, base_lng + 0.12),
            ("CAM22", "BK Mervada tran Rasta", base_lat + 0.13, base_lng + 0.13),
            ("CAM23", "kheram", base_lat + 0.14, base_lng + 0.14),
            ("CAM24", "dehgarn", base_lat + 0.15, base_lng + 0.15),
            ("CAM25", "dhanori", base_lat - 0.10, base_lng - 0.10),
            ("CAM26", "TANKAL", base_lat - 0.11, base_lng - 0.11),
            ("CAM27", "bilimora", base_lat - 0.12, base_lng - 0.12),
            ("CAM28", "bilimora", base_lat - 0.13, base_lng - 0.13),
            ("CAM29", "bilimora", base_lat - 0.14, base_lng - 0.14),
            ("CAM30", "Gandhidham Rambaugh p2", base_lat - 0.15, base_lng - 0.15),
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
