from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.model.role import UserRole
from app.schemas.dependencies import (
    get_current_user, 
    SessionNoteResponse, 
    SessionNoteCreate, 
    SessionNoteUpdate
)
from app.models import GrowthSession, SessionNote, Team, User

router = APIRouter(
    prefix="/sessions/{session_id}/notes",
    tags=["Session Notes"]
)

def check_session_access(session_id: int, db: Session, current_user: User):
    session = db.query(GrowthSession).filter(GrowthSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Growth session not found")
    
    team = db.query(Team).filter(Team.id == session.team_id).first()
    if current_user.role == UserRole.admin:
        return session
    
    if current_user.role == UserRole.lead and team.lead_id == current_user.id:
        return session

    raise HTTPException(status_code=403, detail="Not authorized to access notes for this growth session")

@router.post("/", response_model=SessionNoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(session_id: int, note_in: SessionNoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_session_access(session_id, db, current_user)
    
    note = SessionNote(content=note_in.content, session_id=session_id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

@router.get("/", response_model=list[SessionNoteResponse])
def get_notes(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_session_access(session_id, db, current_user)
    
    return db.query(SessionNote).filter(SessionNote.session_id == session_id).all()

@router.get("/{note_id}", response_model=SessionNoteResponse)
def get_note(session_id: int, note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_session_access(session_id, db, current_user)
    
    note = db.query(SessionNote).filter(SessionNote.id == note_id, SessionNote.session_id == session_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Session note not found")
    return note

@router.patch("/{note_id}", response_model=SessionNoteResponse)
def update_note(session_id: int, note_id: int, note_in: SessionNoteUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_session_access(session_id, db, current_user)
    
    note = db.query(SessionNote).filter(SessionNote.id == note_id, SessionNote.session_id == session_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Session note not found")
    
    if note_in.content is not None:
        note.content = note_in.content
    
    db.commit()
    db.refresh(note)
    return note

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(session_id: int, note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_session_access(session_id, db, current_user)
    
    note = db.query(SessionNote).filter(SessionNote.id == note_id, SessionNote.session_id == session_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Session note not found")
    
    db.delete(note)
    db.commit()
    return None
