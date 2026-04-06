import re
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Notification, TechnicalDebt, DebtComment
from app.model.role import NotificationType, UserRole
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.dependencies import (
    get_current_user, 
    DebtCommentCreate,
    DebtCommentResponse,
)
from app.utils.security import sanitize_text
from fastapi import BackgroundTasks

router = APIRouter(
    prefix="/mentions",
    tags=["Mentions"]
)



def handle_mention(
        comment_text:str,
        db:Session,
        sender_id:int,
        debt_id=int
):
    mentioned_usernames=re.findall(r'@(\w+)',comment_text)
    emails=re.findall(r'[\w\.-]+@[\w\.-]+', comment_text)
    
    users_to_notify = set()

    for username in mentioned_usernames:
        user=db.query(User).filter(User.name==username).first()
        if user:
            users_to_notify.add(user)
            
    for email in emails:
        user=db.query(User).filter(User.email==email).first()
        if user:
            users_to_notify.add(user)

    for user in users_to_notify:
        notification=Notification(user_id=user.id,type=NotificationType.mention,message=f"You were mentioned in a comment: {comment_text}")
        db.add(notification)

    db.commit()






@router.post("/{debt_id}/comments", response_model=DebtCommentResponse)
def add_comment(
    debt_id: int,
    comment_data: DebtCommentCreate,
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    
):
    debt = db.query(TechnicalDebt).filter(TechnicalDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Technical Debt not found")
    
    is_admin = current_user.role == UserRole.admin
    is_team_member = any(m.id == current_user.id for m in debt.project.team.members)
    
    if not (is_admin or is_team_member):
        raise HTTPException(status_code=403, detail="You are not member of the project team, so you cannot comment.")

    comment = DebtComment(
        debt_id=debt_id,
        user_id=current_user.id,
        comment=sanitize_text(comment_data.comment)
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    background_tasks.add_task(
        handle_mention, 
        comment_text=comment_data.comment, 
        db=db, 
        sender_id=current_user.id,
        debt_id=debt_id
    )

    return comment