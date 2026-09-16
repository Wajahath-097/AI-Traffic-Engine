import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.models import Role, User
from app.core.security import hash_password

def seed_demo_users():
    db = SessionLocal()
    try:
        demo_users = [
            {"officer_id": "superadmin", "name": "Super Admin Demo", "password": "admin123", "role": "Super Admin"},
            {"officer_id": "officer1", "name": "Traffic Officer Demo", "password": "officer123", "role": "Traffic Officer"},
            {"officer_id": "control1", "name": "Control Room Demo", "password": "control123", "role": "Control Room"},
            {"officer_id": "analyst1", "name": "Analyst Demo", "password": "analyst123", "role": "Analyst"},
            {"officer_id": "auditor1", "name": "Auditor Demo", "password": "auditor123", "role": "Auditor"},
        ]
        
        for user_data in demo_users:
            # check if exists
            existing = db.query(User).filter(User.officer_id == user_data["officer_id"]).first()
            if existing:
                print(f"User {user_data['officer_id']} already exists.")
                continue
            
            # get role
            role = db.query(Role).filter(Role.name == user_data["role"]).first()
            if not role:
                print(f"Role {user_data['role']} not found. Skipping.")
                continue
                
            new_user = User(
                officer_id=user_data["officer_id"],
                name=user_data["name"],
                password_hash=hash_password(user_data["password"]),
                role_id=role.id,
                is_active=True
            )
            db.add(new_user)
            print(f"Created demo user: {user_data['officer_id']} (Role: {user_data['role']})")
            
        db.commit()
        print("Demo users seeded successfully.")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_users()
