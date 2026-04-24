import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv('DB_CONNECTION')

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("Database connection successful!")
        print(f"Result: {result.fetchone()}")
except Exception as e:
    print(f"Database connection failed: {e}")