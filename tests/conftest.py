
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, get_db
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
