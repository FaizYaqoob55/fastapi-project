from app.database import engine, Base
from app import models

try:
    print("Attempting to create database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
except Exception as e:
    print(f"Failed to create database tables: {e}")
    import traceback
    traceback.print_exc()