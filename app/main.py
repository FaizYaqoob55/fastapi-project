from fastapi import FastAPI, Depends, HTTPException, status, Response
from app.schemas.dependencies import Usercreate, LoginRequest
from app.database import engine, Base, get_db
from sqlalchemy.orm import Session
from app.models import User,Team,TeamMeamber,Users,Project
from app.utils.security import hash_password, verify_password, create_access_token, refresh_access_token, SECRET_KEY, ALGORITHM
import uvicorn
import jwt
from app import models, schemas
from app.routes import admin
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from app.model.role import UserRole

app = FastAPI(title="My FastAPI Application")

# @app.on_event('startup')
# def startup():
Base.metadata.create_all(bind=engine)

app.include_router(admin.router)

# Security schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
bearer_scheme = HTTPBearer()


def _normalize_role_value(raw_role):
    # Support role stored as string, tuple/list, or enum member
    if raw_role is None:
        return None
    if isinstance(raw_role, (list, tuple)) and len(raw_role) > 0:
        return str(raw_role[0])
    return str(raw_role)


def _validate_role_str(role_str: str) -> UserRole | None:
    if role_str is None:
        return None
    # Try matching by name first
    if role_str in UserRole.__members__:
        return UserRole[role_str]
    # Try matching by value (handles enum values that may be tuples)
    for member in UserRole:
        member_val = member.value
        if isinstance(member_val, (list, tuple)):
            compare = str(member_val[0])
        else:
            compare = str(member_val)
        if compare == role_str:
            return member
    return None


def _decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = _decode_token(token)
    email = payload.get("sub")
    raw_role = payload.get("role")
    role_str = _normalize_role_value(raw_role)
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    # Attach resolved role (enum) to user for downstream checks
    validated = _validate_role_str(role_str)
    user._token_role = validated
    return user


def get_current_user_from_bearer(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    return get_current_user(token=token, db=db)


def requires_role(required_role: UserRole, use_bearer: bool = False):
    def _dependency(current_user: models.User = Depends(get_current_user_from_bearer) if use_bearer else Depends(get_current_user)):
        user_role = getattr(current_user, "_token_role", None)
        if user_role is None:
            # fall back to DB-stored role
            user_role = current_user.role
        if user_role != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_user
    return _dependency


@app.post('/user_register')
def register(user:Usercreate,db:Session=Depends(get_db)):
    existing_user=db.query(User).filter(User.email==user.email).first()
    if existing_user:
        raise HTTPException(status_code=400,detail='Email already registered')
    new_user=models.User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {'message':'User created'}

@app.get('/users')
def get_users(db:Session=Depends(get_db)):
    users=db.query(User).all()
    return users



@app.get("/users/{id}", response_model=schemas.UserResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user



@app.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id: int, db: Session = Depends(get_db)):
    user_query = db.query(models.User).filter(models.User.id == id)
    if user_query.first() == None:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
 

@app.put("/users/{id}", response_model=schemas.UserResponse)
def update_user(id: int, updated_user: schemas.UserCreate, db: Session = Depends(get_db)):
    user_query = db.query(models.User).filter(models.User.id == id)
    user = user_query.first()
    
    if user == None:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = updated_user.model_dump()
    user_data['password'] = hash_password(user_data['password']) 
    
    user_query.update(user_data, synchronize_session=False)
    db.commit()
    return user_query.first()

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Works with Swagger "Authorize" (form-data)
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail='Invalid email')

    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail='Invalid password')

    token_data = {"sub": user.email, "role": user.role.value}
    access_token = create_access_token(token_data)
    # Return standard OAuth2 response required by Swagger UI
    return {"access_token": access_token, "token_type": "bearer"}



@app.post("/refresh-token")
def refresh_token(request:LoginRequest,db:Session=Depends(get_db)):
    user=db.query(User).filter(User.email==request.email).first()
    if not user:
        raise HTTPException(status_code=400,detail="Invalid token")
    if not verify_password(request.password,user.password):
        raise HTTPException(status_code=400,detail="Invalid password")
    
    token_data={"sub":user.email,"role":user.role.value}
    refresh_token=refresh_access_token(token_data)
    return {"refresh_token":refresh_token,"token_type":"bearer"}

@app.get('/me')
def my_profile(current_user = Depends(get_current_user)):
    return {
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
        'role': current_user.role
    }





@app.get("/health")
def health():
    return {"status": "database connected"}



if __name__ == "__main__":
    uvicorn.run('main:app',host="0.0.0.0",port=8000, reload=True)
