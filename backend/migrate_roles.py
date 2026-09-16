import sys
import os

# Add backend directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.models import Role, User

def migrate_roles():
    db = SessionLocal()
    try:
        # Define new roles
        new_roles_data = [
            {"name": "Super Admin", "description": "Full system administration"},
            {"name": "Traffic Officer", "description": "Assigned cameras + vehicle searches"},
            {"name": "Control Room", "description": "Live feeds + alerts"},
            {"name": "Analyst", "description": "Reports/statistics"},
            {"name": "Auditor", "description": "Logs only"}
        ]
        
        # Create new roles if they don't exist
        new_roles = {}
        for r_data in new_roles_data:
            role = db.query(Role).filter(Role.name == r_data["name"]).first()
            if not role:
                role = Role(name=r_data["name"], description=r_data["description"])
                db.add(role)
                db.flush() # get id
            new_roles[r_data["name"]] = role
            
        # Get Super Admin role for migration
        super_admin_role = new_roles["Super Admin"]
        
        # Migrate existing users
        users = db.query(User).all()
        for user in users:
            # Reassign all existing users to Super Admin so they aren't locked out
            # Or if they were an officer, maybe to Traffic Officer. Let's make everyone Super Admin for safety
            # since it's a dev environment and they can downgrade later.
            print(f"Migrating user {user.officer_id} to Super Admin...")
            user.role_id = super_admin_role.id
            
        db.commit()
        
        # Now delete old roles
        old_role_names = ["officer", "analyst", "administrator"]
        for old_name in old_role_names:
            old_role = db.query(Role).filter(Role.name == old_name).first()
            if old_role:
                print(f"Deleting old role: {old_name}")
                db.delete(old_role)
                
        db.commit()
        print("Role migration completed successfully.")
        
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_roles()
