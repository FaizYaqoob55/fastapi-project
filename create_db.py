import sys
import os

# Path set karein
sys.path.append(os.getcwd())

# Ab database.py se engine aur Base uthayein
from app.database import engine, Base
# Saare models import karein taake SQLAlchemy ko pata chale kya banana hai
import app.models 


def make_tables():
    try:
        print("Tables banane ki koshish ho rahi hai...")
        # Ye line database.py wala engine use karke tables banaye gi
        Base.metadata.create_all(bind=engine)
        print("Mubarak ho! Tables ban chuki hain.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    make_tables()