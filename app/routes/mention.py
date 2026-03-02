import re
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Notification, TechnicalDebt, DebtComment
from app.model.role import NotificationType
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.dependencies import (
    get_current_user, 
    DebtCommentCreate,
    DebtCommentResponse,
)


router = APIRouter(
    prefix="/mentions",
    tags=["Mentions"]
)



def handle_mention(
        comment_text:str,
        db:Session,
        sender_id:int
):
    mentioned_usernames=re.findall(r'@(\w+)',comment_text)
    for username in mentioned_usernames:
        user=db.query(User).filter(User.name==username).first()
        if user:
            notification=Notification(user_id=user.id,type=NotificationType.mention,message=f"You were mentioned in a comment")
            db.add(notification)
    db.commit()




@router.post("/{debt_id}/comments",response_model=DebtCommentResponse)
def add_comment(
    debt_id:int,
    comment_data:DebtCommentCreate,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    debt=db.query(TechnicalDebt).filter(TechnicalDebt.id==debt_id).first()
    if not debt:
        raise HTTPException(status_code=404,detail="Technical Debt not found")
    
    comment=DebtComment(
        debt_id=debt_id,
        user_id=current_user.id,
        comment=comment_data.comment
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    handle_mention(comment_text=comment_data.comment,db=db,sender_id=current_user.id)

    return comment