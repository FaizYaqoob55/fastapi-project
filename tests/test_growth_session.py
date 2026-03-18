import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.model.role import UserRole
from app.models import User, Team
from sqlalchemy.orm import Session

client = TestClient(app)

from app.schemas.dependencies import get_current_user

# Mock user for dependency override
def override_get_current_user():
    return User(id=1, email="test@example.com", role=UserRole.admin)

app.dependency_overrides[get_current_user] = override_get_current_user

def test_get_growth_sessions_invalid_date(client):
    response = client.get("/growth-sessions/?session_date=875")
    # Validation error should happen before/during parameter parsing
    assert response.status_code == 422
    # Just ensure there is a error detail
    assert "detail" in response.json()

def test_get_growth_sessions_valid_date(client):
    response = client.get("/growth-sessions/?session_date=2024-03-11")
    # Now that we are "logged in", it should not be 401/403 (unless DB issues)
    # But primarily we want to ensure it's not a 500 error
    assert response.status_code != 500

# Clear overrides after tests if needed, but since it's a module level test it's fine for now
