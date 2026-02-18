from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, HTTPException, Query,Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.model.role import SessionStatus, UserRole
from app.routes import team
from app.schemas.dependencies import get_current_user, GrowthSessionResponse, GrowthSessionCreate, GrowthSessionUpdate, SessionNoteResponse, ActionItemResponse
from app.models import ActionItem, GrothSession, SessionNote, Team, User










router = APIRouter(
    prefix="/growth-sessions",
    tags=["Growth Sessions"]
)

# # sub-routers for notes and action items under a specific growth session
# notes_router = APIRouter(prefix='/{session_id}/notes', tags=["Session Notes"])
# action_router = APIRouter(prefix='/{session_id}/action', tags=["Action Items"])





@router.post("/",response_model=GrowthSessionResponse)
def create_growth_session(data: GrowthSessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.lead_id == current_user.id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if current_user.role not in [UserRole.admin, UserRole.lead]:
        raise HTTPException(status_code=403, detail="Not authorized to create growth sessions")
   
    session_data = data.dict()
    session_data['team_id'] = team.id
    session=GrothSession(**session_data)
    db.add(session)
    db.commit() 
    db.refresh(session)
    return session



@router.get("/",response_model=list[GrowthSessionResponse])
def get_growth_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), team_id: Optional[int] = Query(None), status: Optional[str] = Query(None), session_date: Optional[str] = Query(None)):
    query=db.query(GrothSession)
    if team_id :
        team = db.query(Team).filter(Team.lead_id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        query = query.filter(GrothSession.team_id == team.id)
  
    if status:
        query = query.filter(GrothSession.status == status)

    if session_date:
        query = query.filter(GrothSession.date == session_date)
    return query.all()


@router.put("/{session_id}",response_model=GrowthSessionResponse)
def update_growth_session(session_id: int, data: GrowthSessionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(GrothSession).filter(GrothSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Growth session not found")
    team= db.query(Team).filter(Team.id == session.team_id).first()
    if current_user.role not in [UserRole.admin, UserRole.lead] and team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this growth session")
    for key, value in data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(session, key, value)
    db.commit()
    db.refresh(session)
    return session

@router.delete("/{session_id}")
def delete_growth_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(GrothSession).filter(GrothSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Growth session not found")
    team= db.query(Team).filter(Team.id == session.team_id).first()
    if current_user.role not in [UserRole.admin, UserRole.lead] and team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this growth session")
    db.delete(session)
    db.commit()
    return {"detail": "Growth session deleted successfully"}





@router.patch("/{session_id}/status")
def update_growth_session_status(session_id: int, status: str = Body(..., embed=True), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(GrothSession).filter(GrothSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Growth session not found")
    team= db.query(Team).filter(Team.id == session.team_id).first()
    if current_user.role not in [UserRole.admin, UserRole.lead] and team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this growth session")
    if status not in [s.value for s in SessionStatus]:
        raise HTTPException(status_code=400, detail="Invalid status value")
    session.status = status
    db.commit()
    db.refresh(session)
    return {"detail": "Growth session status updated successfully", 'status': status}












