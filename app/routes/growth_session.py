from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.model.role import NotificationType, SessionStatus, UserRole
from app.routes import team
from app.utils.calendar_services import create_calendar_event
from app.schemas.dependencies import (
    get_current_user, 
    GrowthSessionResponse, 
    GrowthSessionCreate, 
    GrowthSessionUpdate
)
from app.models import GrowthSession, Team, User
from app.utils.ics_generator import generate_ics_file
from fastapi.responses import Response

from app.utils.notifications import create_notification, dispatch_notification_email
from app.utils.security import sanitize_text
from fastapi import BackgroundTasks
router = APIRouter(
    prefix="/growth-sessions",
    tags=["Growth Sessions"]
)

# Schemas file mein ye check karein:
# class GrowthSessionCreate(BaseModel):
#     title: str
#     date: date        # Example: 2024-03-24
#     start_time: time  # Example: 14:30
#     end_time: time    # Example: 15:30
#     team_id: int

@router.post("/", response_model=GrowthSessionResponse, status_code=status.HTTP_201_CREATED)
def create_growth_session(
    data: GrowthSessionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # RBAC checks
    if current_user.role not in [UserRole.admin, UserRole.lead]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    team_obj = db.query(Team).filter(Team.id == data.team_id).first()
    if not team_obj:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if current_user.role != UserRole.admin and team_obj.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the team lead or admin can create sessions")

    # Title sanitize karein
    clean_title = sanitize_text(data.title)
    
    session = GrowthSession(
        title=clean_title,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        team_id=data.team_id,
        status=SessionStatus.planned
    )

    # Database mein pehle save karein taake ID mil jaye
    db.add(session)
    db.commit()
    db.refresh(session)

    # Ab calendar event create karein (Background task mein bhi dal sakte hain)
    try:
        calendar_event_id = create_calendar_event(session)
        session.calendar_event_id = calendar_event_id
        db.commit()
    except Exception as e:
        print(f"Calendar Error: {e}") # Sirf log karein taake session create ho jaye

    # Notifications Loop
    for member in team_obj.members:
        # Internal Notification
        create_notification(db=db, user_id=member.id, type=NotificationType.session_reminder, message=f"New session: {clean_title}")
        
        # Email with ICS (ICS attachment logic yahan call hogi)
        dispatch_notification_email(
            background_task=background_tasks, 
            user=member, 
            notification_type=NotificationType.session_reminder,
            payload={
                'session_title': clean_title, 
                'session_date': str(data.date),
                'start_time': str(data.start_time)
            }
        )

    return session

@router.get('/{id}/calendar-export')
def export_calendar_ics(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(GrowthSession).filter(GrowthSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Growth session not found")
    
    team = db.query(Team).filter(Team.id == session.team_id).first()
    is_member = any(m.id == current_user.id for m in team.members)
    is_lead = team.lead_id == current_user.id
    is_admin = current_user.role == UserRole.admin

    
    if not (is_admin or is_lead or is_member):
        raise HTTPException(status_code=403, detail="Not authorized to export calendar for this growth session")
    try:
        calendar = generate_ics_file(session)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return Response(
        content=calendar, # calendar is already serialized
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=growth_session_{id}.ics"}
    )




@router.get("/", response_model=list[GrowthSessionResponse])
def get_growth_sessions(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
    team_id: Optional[int] = Query(None), 
    status: Optional[SessionStatus] = Query(None), 
    session_date: Optional[date] = Query(None)
):
    query = db.query(GrowthSession)
    if team_id:
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        is_member = any(m.id == current_user.id for m in team.members)
        if current_user.role != UserRole.admin and team.lead_id != current_user.id and not is_member:
            raise HTTPException(status_code=403, detail="Not authorized to view this team's sessions")
              
    if team_id:
        query = query.filter(GrowthSession.team_id == team_id)
  
    if status:
        query = query.filter(GrowthSession.status == status)

    if session_date:
        query = query.filter(GrowthSession.date == session_date)
        
    return query.all()

@router.get("/{session_id}", response_model=GrowthSessionResponse)
def get_growth_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(GrowthSession).filter(GrowthSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Growth session not found")
    team_obj = db.query(Team).filter(Team.id == session.team_id).first()
    is_member = any(m.id == current_user.id for m in team_obj.members)
    if current_user.role != UserRole.admin and team_obj.lead_id != current_user.id and not is_member:
        raise HTTPException(status_code=403, detail="Not authorized to view this team's sessions")
    return session

@router.put("/{session_id}", response_model=GrowthSessionResponse)
def update_growth_session(session_id: int, data: GrowthSessionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # allow updating of time fields as well
    session = db.query(GrowthSession).filter(GrowthSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Growth session not found")
    
    team = db.query(Team).filter(Team.id == session.team_id).first()
    if current_user.role != UserRole.admin and team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this growth session")
    
    for key, value in data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(session, key, value)
    
    session.title = sanitize_text(session.title)
    db.commit()
    db.refresh(session)
    return session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_growth_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(GrowthSession).filter(GrowthSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Growth session not found")
    
    team = db.query(Team).filter(Team.id == session.team_id).first()
    if current_user.role != UserRole.admin and team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this growth session")
    
    db.delete(session)
    db.commit()
    return None

@router.patch("/{session_id}/status", response_model=GrowthSessionResponse)
def update_growth_session_status(session_id: int, status: SessionStatus = Body(..., embed=True), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(GrowthSession).filter(GrowthSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Growth session not found")
    
    team = db.query(Team).filter(Team.id == session.team_id).first()
    if current_user.role != UserRole.admin and team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this growth session")
    
    session.status = status
    db.commit()
    db.refresh(session)
    return session
