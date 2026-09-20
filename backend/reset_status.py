import os
import sys

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.models import Camera

db = SessionLocal()
try:
    cameras = db.query(Camera).all()
    for cam in cameras:
        cam.status = "online"
    db.commit()
    print(f"Updated {len(cameras)} cameras to online status.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
