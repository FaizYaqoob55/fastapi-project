from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.model.role import UserRole, Action_Status
from app.schemas.dependencies import (
    get_current_user, 
    ActionItemResponse, 
    ActionItemCreate, 
    ActionItemUpdate
)
from app.models import GrowthSession, ActionItem, Team, User

router = APIRouter(
    prefix="/sessions/{session_id}/action-items",
    tags=["Action Items"]
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

    raise HTTPException(status_code=403, detail="Not authorized to access action items for this growth session")

@router.post("/", response_model=ActionItemResponse, status_code=status.HTTP_201_CREATED)
def create_action_item(session_id: int, item_in: ActionItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_session_access(session_id, db, current_user)
    
    action_item = ActionItem(
        title=item_in.title,
        status=item_in.status or Action_Status.pending,
        session_id=session_id,
        completed=False
    )
    db.add(action_item)
    db.commit()
    db.refresh(action_item)
    return action_item

@router.get("/", response_model=list[ActionItemResponse])
def get_action_items(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_session_access(session_id, db, current_user)
    
    return db.query(ActionItem).filter(ActionItem.session_id == session_id).all()

@router.get("/{item_id}", response_model=ActionItemResponse)
def get_action_item(session_id: int, item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_session_access(session_id, db, current_user)
    
    item = db.query(ActionItem).filter(ActionItem.id == item_id, ActionItem.session_id == session_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    return item

@router.patch("/{item_id}", response_model=ActionItemResponse)
def update_action_item(session_id: int, item_id: int, item_in: ActionItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_session_access(session_id, db, current_user)
    
    item = db.query(ActionItem).filter(ActionItem.id == item_id, ActionItem.session_id == session_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    
    if item_in.title is not None:
        item.title = item_in.title
    if item_in.status is not None:
        item.status = item_in.status
        if item_in.status == Action_Status.completed:
            item.completed = True
        else:
            item.completed = False
            
    if item_in.completed is not None:
        item.completed = item_in.completed
        if item_in.completed:
            item.status = Action_Status.completed
    
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_action_item(session_id: int, item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_session_access(session_id, db, current_user)
    
    item = db.query(ActionItem).filter(ActionItem.id == item_id, ActionItem.session_id == session_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    
    db.delete(item)
    db.commit()
    return None
