import random
import uuid
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.models import Camera, VehicleDetection, Alert, Journey, JourneyEvent, BlacklistEntry, User
import math

def seed_mock_data():
    db = SessionLocal()
    try:
        # Clear existing
        print("Clearing old data...")
        db.query(JourneyEvent).delete()
        db.query(Journey).delete()
        db.query(Alert).delete()
        db.query(VehicleDetection).delete()
        db.query(BlacklistEntry).delete()
        db.query(Camera).delete()
        db.commit()

        # Create 6 Cameras (1, 2, 3 online, 4, 5, 6 offline)
        print("Creating cameras...")
        base_lat, base_lng = 40.7128, -74.0060 # NYC
        cameras = []
        for i in range(6):
            is_online = i < 3
            cam = Camera(
                camera_id=f"CAM-{i+1:03d}",
                name=f"Intersection {i+1}",
                location=f"Zone {chr(65+i)}",
                latitude=base_lat + random.uniform(-0.02, 0.02),
                longitude=base_lng + random.uniform(-0.02, 0.02),
                status="online" if is_online else "offline",
                enabled=is_online,
                last_heartbeat=datetime.utcnow() if is_online else None
            )
            db.add(cam)
            cameras.append(cam)
        db.commit()
        
        # Generate Indian Number Plates exclusively from Telangana (TS)
        states = ["MH"]
        letters = ["AA", "AB", "CA", "XY", "ZZ", "MK", "TR", "EU", "ES"]
        plates = [f"{random.choice(states)}{random.randint(10,99)}{random.choice(letters)}{random.randint(1000,9999)}" for _ in range(200)]
        detections = []
        now = datetime.utcnow()
        seen_plates = set()
        for i in range(1500):
            # Generate realistic traffic patterns: peak hours 8-10 AM and 5-7 PM
            hour_offset = random.uniform(0, 24)
            hour_of_day = (now - timedelta(hours=hour_offset)).hour
            
            # If not in peak hour, sometimes skip to simulate lower traffic
            if hour_of_day not in [8, 9, 10, 17, 18, 19]:
                if random.random() > 0.4:
                    # Skip to reduce volume in off-peak
                    continue
                    
            # Ensure unique MH plates
            plate = random.choice(plates)
            attempts = 0
            while plate in seen_plates and attempts < 10:
                plate = random.choice(plates)
                attempts += 1
            seen_plates.add(plate)
            det = VehicleDetection(
                camera_id=random.choice(cameras).id,
                plate_number=plate,
                plate_confidence=random.uniform(0.7, 0.99),
                vehicle_class=random.choice(["car", "bus", "auto", "bike", "other"]),
                vehicle_color=random.choice(["white", "white", "black", "silver", "red", "blue"]),
                vehicle_confidence=random.uniform(0.8, 0.99),
                detected_at=now - timedelta(hours=hour_offset),
                ocr_engine="paddleocr",
                ocr_language="en",
                ocr_recheck_count=random.randint(0, 2)
            )
            db.add(det)
            detections.append(det)
        db.commit()

        # Skip Blacklist creation for presentation consistency
        # Print statement retained for debugging
        print("Skipping blacklist entries creation...")
        
        # Create Alerts
        print("Creating alerts...")
        alert_reasons = [
            "Stolen vehicle detected",
            "Pending challans vehicle detected",
            "Suspicious loitering identified",
            "Over-speeding vehicle captured",
            "Red light jump detected",
            "Unauthorized vehicle in restricted lane"
        ]
        for i in range(10):
            plate = random.choice(plates)
            alert_type = "anomaly"
            severity = random.choice(["high", "medium", "critical"])
            msg = f"{random.choice(alert_reasons)} at {random.choice(cameras).name}"
            
            # Create a single alert for the detection
            alert = Alert(
                severity=severity,
                alert_type=alert_type,
                plate_number=plate,
                message=msg,
                camera_id=random.choice(cameras).id,
                # Duplicate alert block removed
                status=random.choice(["open", "investigating"]),
                created_at=now - timedelta(hours=random.uniform(0, 12))
            )
            db.add(alert)
        db.commit()

        # Reconstruct some journeys (simulate movement)
        print("Creating journeys...")
        for plate in plates[:10]:
            plate_dets = sorted([d for d in detections if d.plate_number == plate], key=lambda x: x.detected_at)
            if len(plate_dets) > 1:
                j = Journey(
                    plate_number=plate,
                    start_time=plate_dets[0].detected_at,
                    end_time=plate_dets[-1].detected_at,
                    confidence=sum(d.plate_confidence for d in plate_dets)/len(plate_dets),
                    start_camera_id=plate_dets[0].camera_id,
                    end_camera_id=plate_dets[-1].camera_id
                )
                db.add(j)
                db.commit()
                for idx, d in enumerate(plate_dets):
                    je = JourneyEvent(
                        journey_id=j.id,
                        detection_id=d.id,
                        sequence_number=idx+1
                    )
                    db.add(je)
                db.commit()

        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_mock_data()
