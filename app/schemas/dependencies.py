from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from app.model.role import UserRole,Action_Status,SessionStatus,NotificationType,DebtPriority,DebtStatus
from app.database import get_db
from app.models import User
from app.utils.security import ALGORITHM, SECRET_KEY
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from datetime import date,datetime


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
    title: Optional[str] = Field(None, alias='title')
    completed: Optional[bool] = None
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
    start_time:datetime
    end_time:Optional[datetime] = None

class GrowthSessionCreate(GrowthSessionBase):
    team_id:int

class GrowthSessionUpdate(BaseModel):
    title:Optional[str]=None
    date:date
    start_time:Optional[datetime] = None
    end_time:Optional[datetime] = None

class GrowthSessionResponse(GrowthSessionBase):
    id:int 
    status:SessionStatus
    team_id:int
    calendar_event_id:Optional[str] = None
    meeting_link:Optional[str] = None
    location:Optional[str] = None
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


class NotificationResponse(BaseModel):
    id :int
    type:NotificationType
    message:str
    is_read:bool
    created_at:datetime
    class Config:
        from_attributes =True


class UserPrefrencesUpdate(BaseModel):
    email_session_reminder:Optional[bool]
    email_action_item_due:Optional[bool]
    email_mentions:Optional[bool]





class DebtCommentCreate(BaseModel):
    comment:str

class DebtCommentResponse(BaseModel):
    id:int
    user_id:int
    comment:str
    created_at:datetime
    class Config:
        from_attributes=True


class TechnicalDebtCreate(BaseModel):
    project_id:int
    owner_id:int
    title:str
    description:Optional[str]=None
    priority:DebtPriority=DebtPriority.medium
    severity:Optional[int]=None
    estimated_effort:Optional[int]=None
    due_date:Optional[date]=None


class TechnicalDebtUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[DebtPriority] = None
    status: Optional[DebtStatus] = None
    severity: Optional[int] = None
    estimated_effort: Optional[int] = None
    actual_effort: Optional[int] = None
    due_date: Optional[date] = None


class TechnicalResponse(BaseModel):
    id:int
    project_id:int
    owner_id:int
    title:str
    description:Optional[str]
    priority:DebtPriority
    status:DebtStatus
    severity:Optional[int]
    estimated_effort:Optional[int]
    actual_effort:Optional[int]
    due_date:Optional[date]
    created_at:datetime
    comments:list[DebtCommentResponse]=[]
    class Config:
        from_attributes=True

class PriorityUpdate(BaseModel):
    priority: DebtPriority











































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

