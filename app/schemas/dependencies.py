from arrow import now
from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from app.model.role import UserRole,Action_Status,SessionStatus,NotificationType,DebtPriority,DebtStatus,DeprecationType,TimeLineStage
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
    start_time:datetime = now().strftime("%Y-%m-%d %H:%M:%S")
    end_time:datetime = now().strftime("%Y-%m-%d %H:%M:%S")

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



class ProjectDebtCount(BaseModel):
    project_name: str
    debt_count: int

class MonthlyTrendItem(BaseModel):
    month: str
    debt_count: int

class TechnicalDebtDashboardResponse(BaseModel):
    total_debts: int
    priority_breakdown: dict[str, int]
    by_status: dict[str, int]
    project_breakdown: list[ProjectDebtCount]
    monthly_trend: list[MonthlyTrendItem]
    again_count: int

    class Config:
        from_attributes = True







class DeprecationTimelineBase(BaseModel):
    stage:TimeLineStage
    notes:Optional[str]=None

class DeprecationTimelineCreate(DeprecationTimelineBase):
    planned_date:date
    pass 



class DeprecationTimelineResponse(DeprecationTimelineBase):
    id:int
    created_at:datetime
    planned_date:date
    class Config:
        from_attributes=True





class deprecationsBase(BaseModel):
    project_id:int
    item_name:str
    type:DeprecationType
    current_version:Optional[str]=None
    deprecated_in:Optional[str]=None
    removal_planned_for:Optional[str]=None
    replacement:Optional[str]=None
    affected_systems:Optional[str]=None
    affected_users_count:Optional[int]=0
    impact_level:Optional[str]=None
    migration_notes:Optional[str]=None
    status:Optional[str]=None

class deprecationsCreate(deprecationsBase):
    pass

class deprecationsUpdate(BaseModel):
    project_id:Optional[int]=None
    type:Optional[DeprecationType]=None
    current_version:Optional[str]=None
    deprecated_in:Optional[str]=None
    removal_planned_for:Optional[str]=None
    replacement:Optional[str]=None
    impact_level:Optional[str]=None
    affected_systems:Optional[str]=None
    affected_users_count:Optional[int]=None
    migration_notes:Optional[str]=None

class deprecationsResponse(deprecationsBase):
    id:int
    created_at:datetime
    timeline:list[DeprecationTimelineResponse]=[]
    class Config:
        from_attributes=True





class ImpactReport(BaseModel):
    item_name:str
    impact_level:str
    affected_system:str
    affected_users_count:int
    upcoming_milestones:list[DeprecationTimelineResponse]
    linked_debt_count:int





















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

