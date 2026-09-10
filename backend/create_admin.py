from app.database import SessionLocal
from app.models.models import User, Role
from app.core.security import hash_password

def create_admin():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.officer_id == "admin").first()
        if not admin:
            role = db.query(Role).filter(Role.name == "admin").first()
            if not role:
                role = Role(name="admin", description="System Administrator")
                db.add(role)
                db.commit()
                db.refresh(role)
                
            new_user = User(
                officer_id="admin",
                password_hash=hash_password("admin123"),
                name="System Admin",
                role_id=role.id,
                is_active=True
            )
            db.add(new_user)
            db.commit()
            print("Admin user created successfully! Officer ID: admin, Password: admin123")
        else:
            print("Admin user already exists! Officer ID: admin")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
