from fastapi import FastAPI, Depends, HTTPException, status, Response, Request, Body
from app.schemas.dependencies import Usercreate, LoginRequest, get_current_user, requires_role, UserResponse, bearer_scheme
from app.database import engine, Base, get_db
from sqlalchemy.orm import Session
from app.models import User, Team, TeamMember, Project
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
import uvicorn
from app import models
from app.routes import action_item, admin, growth_session, mention, project, session_note, team,users,technical_debt, deprecation,deprecation_timeline,comments
from fastapi.security import OAuth2PasswordRequestForm
from app.model.role import UserRole
from app.utils import notifications
from app.routes.dashboard import router as dashboard_router
from app.ratelimit import limiter


app = FastAPI(
    title="My FastAPI Application",
    swagger_ui_parameters={"persistAuthorization": True}
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My FastAPI Application",
        version="0.1.0",
        description="API Documentation with JWT Bearer support",
        routes=app.routes,
    )
    # Register the scheme
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    
    # Apply security globally to routes that already have security requirements
    for path in openapi_schema.get("paths", {}).values():
        for method in path.values():
            if "security" in method:
                # Add BearerAuth as an alternative to existing schemes
                if not any("BearerAuth" in s for s in method["security"]):
                    method["security"].append({"BearerAuth": []})
            else:
                # Optional: If you want all routes to have it by default, you'd add it here
                # but it's safer to only add it to routes that already have security.
                pass

    app.openapi_schema = openapi_schema
    return app.openapi_schema

from fastapi.openapi.utils import get_openapi
app.openapi = custom_openapi

app.state.limiter = limiter
# Create database tables
Base.metadata.create_all(bind=engine)



# Include routers
app.include_router(admin.router)
app.include_router(dashboard_router)
app.include_router(team.router)
app.include_router(project.router)
app.include_router(growth_session.router)
app.include_router(session_note.router)
app.include_router(action_item.router)
app.include_router(notifications.router)
app.include_router(users.router)
app.include_router(technical_debt.router)
app.include_router(comments.router)
app.include_router(mention.router)
app.include_router(deprecation.router)
app.include_router(deprecation_timeline.router)



import collections
if not hasattr(collections, 'Mapping'):
    import collections.abc
    collections.Mapping = collections.abc.Mapping
@app.post('/user_register')
def register(user: Usercreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail='Email already registered')
    new_user = models.User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {'message': 'User created'}

@app.get('/users', response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@app.get("/users/{id}", response_model=UserResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id: int, db: Session = Depends(get_db)):
    user_query = db.query(models.User).filter(models.User.id == id)
    if user_query.first() is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.put("/users/{id}", response_model=UserResponse)
def update_user(id: int, updated_user: Usercreate, db: Session = Depends(get_db)):
    user_query = db.query(models.User).filter(models.User.id == id)
    user = user_query.first()
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email != updated_user.email:
        existing_user = db.query(User).filter(User.email == updated_user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail='Email already registered')
    
    user_data = updated_user.model_dump()
    user_data['password'] = hash_password(user_data['password']) 
    
    user_query.update(user_data, synchronize_session=False)
    db.commit()
    return user_query.first()


@app.post("/login")
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    token_data = {"sub": user.email, "role": user.role.value}
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }


@app.get('/me')
@limiter.limit("5/minute")
def my_profile(request: Request, current_user: User = Depends(get_current_user)):
    return {
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
        'role': current_user.role
    }

@app.get("/health")
def health():
    return {"status": "Ok"}

if __name__ == "__main__":
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)
