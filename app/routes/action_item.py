from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, HTTPException, Query,Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.model.role import SessionStatus, UserRole
from app.routes import team
from app.schemas.dependencies import get_current_user, GrowthSessionResponse, GrowthSessionCreate, GrowthSessionUpdate, SessionNoteResponse, ActionItemResponse
from app.models import ActionItem, GrothSession, SessionNote, Team, User



router = APIRouter(
    prefix="/sessions/{session_id}/notes",
    tags=["Session Notes"]
)


@router.post('/action-items', response_model=ActionItemResponse)
def add_action_item(session_id: int, description: str = Body(..., embed=True), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(GrothSession).filter(GrothSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Growth session not found")
    team= db.query(Team).filter(Team.id == session.team_id).first()
    if current_user.role not in [UserRole.admin, UserRole.lead] and team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add action items to this growth session")
    action_item = ActionItem(description=description, session_id=session_id)
    db.add(action_item)
    db.commit()
    db.refresh(action_item)
    return action_item