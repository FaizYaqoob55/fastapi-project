from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from app.model.role import UserRole,Action_Status,SessionStatus
from app.database import get_db
from app.models import User
from app.utils.security import ALGORITHM, SECRET_KEY
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from datetime import date


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


class SessionNoteBase(BaseModel):
    content: str

class SessionNoteCreate(SessionNoteBase):
    pass

class SessionNoteUpdate(BaseModel):
    content: Optional[str] = None

class SessionNoteResponse(SessionNoteBase):
    id:int
    class Config:
        from_attributes=True




class ActionItemBase(BaseModel):
    title: str = Field(alias='titlr')
    status: Optional[Action_Status] = None


class ActionItemCreate(ActionItemBase):
    pass

class ActionItemUpdate(BaseModel):
    title: Optional[str] = Field(None, alias='titlr')
    status: Optional[Action_Status] = None

class ActionItemResponse(ActionItemBase):
    id: int
    completed: bool
    
    class Config:
        from_attributes = True
        populate_by_name = True


class GrowthSessionBase(BaseModel):
    title:str
    date:date

class GrowthSessionCreate(GrowthSessionBase):
    team_id:int

class GrowthSessionUpdate(BaseModel):
    title:Optional[str]=None
    date:Optional[date]=None

class GrowthSessionResponse(GrowthSessionBase):
    id:int 
    status:SessionStatus
    team_id:int

    notes:list[SessionNoteResponse]=[]
    action_items:list[ActionItemResponse]=[]

    class Config:
        from_attributes=True


class Usercreate(BaseModel):
    name:str
    password:str
    email:EmailStr

class UserResponse(BaseModel):
    id:int
    name:str
    email:EmailStr

    class Config():
        from_attributes=True

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

