import random
from app.database import SessionLocal, engine
from app.models.models import RegisteredVehicle, Base

def seed_rto_database():
    db = SessionLocal()
    try:
        Base.metadata.create_all(bind=engine)
        db.query(RegisteredVehicle).delete()
        db.commit()
        print("Seeding Simulated RTO Database...")
        vehicles = [
            {"plate_number": "MH02FH9304", "vehicle_class": "car", "vehicle_color": "black", "owner_name": "Rajesh Kumar", "registration_status": "Active"},
            {"plate_number": "MH09EU1234", "vehicle_class": "auto", "vehicle_color": "yellow", "owner_name": "Suresh Auto Travels", "registration_status": "Active"},
            {"plate_number": "MH09PA5678", "vehicle_class": "auto", "vehicle_color": "yellow", "owner_name": "Ramesh Singh", "registration_status": "Active"},
            {"plate_number": "MH29XX9999", "vehicle_class": "car", "vehicle_color": "silver", "owner_name": "Anita Desai", "registration_status": "Active"},
            {"plate_number": "MH07EZ8888", "vehicle_class": "car", "vehicle_color": "blue", "owner_name": "Fake Identity", "registration_status": "Active"},
            {"plate_number": "MH08AB1234", "vehicle_class": "bus", "vehicle_color": "red", "owner_name": "Stolen Transport", "registration_status": "Stolen"},
        ]
        states = ["MH", "TS", "AP", "KA", "DL"]
        classes = ["car", "bus", "auto", "bike", "truck"]
        colors = ["white", "black", "silver", "red", "blue", "yellow", "green", "gray"]
        for _ in range(100):
            plate = f"{random.choice(states)}{random.randint(10,99)}{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))}{random.randint(1000,9999)}"
            vehicles.append({
                "plate_number": plate,
                "vehicle_class": random.choice(classes),
                "vehicle_color": random.choice(colors),
                "owner_name": f"Citizen {random.randint(1000, 9999)}",
                "registration_status": random.choice(["Active", "Active", "Active", "Expired", "Stolen"])
            })
        for v in vehicles:
            existing = db.query(RegisteredVehicle).filter(RegisteredVehicle.plate_number == v["plate_number"]).first()
            if not existing:
                record = RegisteredVehicle(**v)
                db.add(record)
        db.commit()
        print("RTO Database successfully seeded.")
    except Exception as e:
        print(f"Error seeding RTO DB: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_rto_database()
