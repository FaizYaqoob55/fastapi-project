from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.model.role import UserRole
from app.database import get_db
from app.models import User
from app.utils.security import ALGORITHM, SECRET_KEY
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


class TeamCreate(BaseModel):
    name: str

class TeamUpdate(BaseModel):
    name: Optional[str] = None


class TeamResponse(BaseModel):
    id: int
    name: str
    lead_id: int

    class Config:
        from_attributes = True


class TeamMemberCreate(BaseModel):
    user_id: int


class Usercreate(BaseModel):
    name:str
    password:str
    email:EmailStr

class UserResponse(BaseModel):
    id:int
    name:str
    email:EmailStr

    class Config():
        for_attributes=True

class LoginRequest(BaseModel):
    email:EmailStr
    password:str


def get_current_user(
    token:str=Depends(oauth2_scheme),  
    db:Session=Depends(get_db)):
    credentials_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate":"Bearer"},
    )
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user=db.query(User).filter(User.email==email).first()
    if user is None:
        raise credentials_exception
    return user




def requires_role(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role.value != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


