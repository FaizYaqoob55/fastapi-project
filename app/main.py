from fastapi import FastAPI,Depends,HTTPException,status,Response
from app.schemas.dependencies import Usercreate ,LoginRequest
from app.database import engine,Base,Sessionlocal
from sqlalchemy.orm import Session
from app.models import User
from app.utils.security import hash_password, verify_password
import uvicorn
import jwt
from app import models
from . import models, schemas
from app.utils.security import create_access_token, refresh_access_token


app = FastAPI(title="My FastAPI Application")

# @app.on_event('startup')
# def startup():
Base.metadata.create_all(bind=engine)

def get_db():
    db=Sessionlocal()
    try :
        yield db 
    finally:
        db.close()
        
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
def login(request:LoginRequest,db:Session=Depends(get_db)):
    user=db.query(User).filter(User.email==request.email).first()
    if not user:
        raise HTTPException(status_code=400,detail='Invalid email ')
    
    if not verify_password(request.password,user.password):
        raise HTTPException(status_code=400,detail='Invalid  password')
    
    token_data = {"sub": user.email}
    access_token = create_access_token(token_data)
    refresh_token = refresh_access_token(token_data)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@app.post("/refresh-token")
def refresh_token(request:LoginRequest,db:Session=Depends(get_db)):
    user=db.query(User).filter(User.email==request.email).first()
    if not user:
        raise HTTPException(status_code=400,detail="Invalid token")
    if not verify_password(request.password,user.password):
        raise HTTPException(status_code=400,detail="Invalid password")
    
    token_data={"sub":user.email}
    refresh_token=refresh_access_token(token_data)
    return {"refresh_token":refresh_token,"token_type":"bearer"}






@app.get("/health")
def health():
    return {"status": "database connected"}



if __name__ == "__main__":
    uvicorn.run('main:app',host="0.0.0.0",port=8000, reload=True)
