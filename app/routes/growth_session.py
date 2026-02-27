from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.model.role import NotificationType, SessionStatus, UserRole
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

router = APIRouter(
    prefix="/growth-sessions",
    tags=["Growth Sessions"]
)

@router.post("/", response_model=GrowthSessionResponse, status_code=status.HTTP_201_CREATED)
def create_growth_session(data: GrowthSessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    if current_user.role not in [UserRole.admin, UserRole.lead]:
        raise HTTPException(status_code=403, detail="Not authorized to create growth sessions")
    
    team = db.query(Team).filter(Team.id == data.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if current_user.role != UserRole.admin and team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the team lead or admin can create sessions for this team")
    

    session = GrowthSession(
        title=data.title,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        team_id=data.team_id,
        status=SessionStatus.planned
    )
    notification=create_notification(
        db=db,
        user_id=current_user.id,
        type=NotificationType.session_reminder,
        message=f"Your growth session \"{data.title}\" is scheduled"
    )
    dispatch_notification_email(
        background_task=Depends(),
        user=current_user,
        notification_type=NotificationType.session_reminder,
        payload={
            'session_title':data.title,
            'session_date':data.date
        }
    )
    calendar_event_id = create_calendar_event(session)
    session.calendar_event_id = calendar_event_id
    db.add(session)
    db.commit() 
    db.refresh(session)
    return session



@router.get('/{id}/calendar-export')
def export_calendar_ics(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(GrowthSession).filter(GrowthSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Growth session not found")
    
    team = db.query(Team).filter(Team.id == session.team_id).first()
    if current_user.role != UserRole.admin and team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to export calendar event for this growth session")
    try:
        calendar = generate_ics_file(session)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return Response(
        content=str(calendar),
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=growth_session_{id}.ics"}
    )
  



@router.get("/", response_model=list[GrowthSessionResponse])
def get_growth_sessions(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
    team_id: Optional[int] = Query(None), 
    status: Optional[SessionStatus] = Query(None), 
    session_date: Optional[str] = Query(None)
):
    query = db.query(GrowthSession)
    
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
