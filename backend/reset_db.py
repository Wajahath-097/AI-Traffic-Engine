import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database import engine
from app.models.models import Base

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Database schema reset complete!")
