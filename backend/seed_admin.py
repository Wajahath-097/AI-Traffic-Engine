import sys
from app.database import SessionLocal
from app.models.models import User, Role
from app.core.security import hash_password

def seed_admin():
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(User.officer_id == "admin").first()
        if existing:
            print("Admin user already exists.")
            return

        # Get admin role
        admin_role = db.query(Role).filter(Role.name == "administrator").first()
        if not admin_role:
            print("Admin role not found. Please restart the backend to initialize roles.")
            return

        # Create admin user
        admin_user = User(
            officer_id="admin",
            password_hash=hash_password("admin123"),
            name="System Admin",
            role_id=admin_role.id,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully! ID: admin, Password: admin123")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
