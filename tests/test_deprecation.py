from app.main import app
from app.schemas.dependencies import get_current_user


from app.main import app
from app.schemas.dependencies import get_current_user

# Mock user data
async def override_get_current_user():
    return {"id": 1, "username": "testuser", "role": "admin"}

# App ki dependency ko override karein
app.dependency_overrides[get_current_user] = override_get_current_user



def override_get_current_user():
    from app.models import User
    from app.model.role import UserRole
    return User(id=1, email="test@example.com", name="test", role=UserRole.admin)

app.dependency_overrides[get_current_user] = override_get_current_user

def test_get_deprecation(client):
    response = client.get("/deprecations/deprecation")
    assert response.status_code == 200

def test_create_deprecation(client):
    data={
        "project_id": 1,
        "item_name": "Test Deprecation",
        "type": "api", 
        "reason": "Deprecation",
        "status": "Deprecation"
    }
    response = client.post("/deprecations/deprecation", json=data)
    assert response.status_code in [200, 404, 201]

