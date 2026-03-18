from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session,joinedload
from sqlalchemy import asc, desc
from app.database import get_db
from app.models import Project
from app.schemas.dependencies import (
    get_current_user, 
    TechnicalResponse,
    TechnicalDebtCreate,
    TechnicalDebtUpdate,
    DebtCommentCreate,
    DebtCommentResponse,
    PriorityUpdate
)
from app.models import Project, TechnicalDebt, User, DebtComment,DebtStatusHistory
from app.model.role import DebtPriority,DebtStatus,UserRole
from fastapi import Body
from app.utils.security import sanitize_text
from app.ratelimit import limiter

router = APIRouter(
    prefix="/comments",
    tags=["Comments"]
)



@router.post(
    "/{debt_id}/comments",
    response_model=DebtCommentResponse
)
def add_debt_comment(
    debt_id: int,
    data: DebtCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    debt = db.query(TechnicalDebt).filter(
        TechnicalDebt.id == debt_id
    ).first()

    if not debt:
        raise HTTPException(
            status_code=404,
            detail="Technical Debt not found"
        )
    if current_user.role != UserRole.admin and debt.owner_id != current_user.id:
        raise HTTPException(status_code=403,detail="Not authorized to add comment to this technical debt")

    comment = DebtComment(
        debt_id=debt_id,
        user_id=current_user.id,
        comment=sanitize_text(data.comment)
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment




@router.get(
    "/{debt_id}/comments",
    response_model=list[DebtCommentResponse]
)
def get_debt_comments(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    debt = db.query(TechnicalDebt).filter(
        TechnicalDebt.id == debt_id
    ).first()
    if not debt:
        raise HTTPException(
            status_code=404,
            detail="Technical Debt not found"
        )
    if current_user.role != UserRole.admin and debt.owner_id != current_user.id:
        raise HTTPException(status_code=403,detail="Not authorized to view comments of this technical debt")
    return db.query(DebtComment).filter(
        DebtComment.debt_id == debt_id
    ).order_by(DebtComment.created_at.desc()).all()




@router.delete("/comments/{comment_id}")
def delete_debt_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = db.query(DebtComment).filter(
        DebtComment.id == comment_id
    ).first()

    if not comment:
        raise HTTPException(status_code=404,detail="Comment not found")
    debt = db.query(TechnicalDebt).filter(
        TechnicalDebt.id == comment.debt_id
    ).first()   
    if not debt:
        raise HTTPException(status_code=404,detail="Technical Debt not found")
    if current_user.role != UserRole.admin and debt.owner_id != current_user.id:
        raise HTTPException(status_code=403,detail="Not authorized to delete this comment")
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}



