from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.schemas.dependencies import (
    get_current_user, 
    DebtCommentCreate,
    DebtCommentResponse,
)
from app.models import TechnicalDebt, User, DebtComment
from app.model.role import UserRole
from app.utils.security import sanitize_text

router = APIRouter(
    prefix="/comments",
    tags=["Comments"]
)



@router.post("/{debt_id}/comments", response_model=DebtCommentResponse)
def add_debt_comment(
    debt_id: int,
    data: DebtCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch Debt with Project/Team info
    debt = db.query(TechnicalDebt).filter(TechnicalDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Technical Debt not found")

    # 2. Kya user is project ki team ka member hai?
    is_admin = current_user.role == UserRole.admin
    is_team_member = any(m.id == current_user.id for m in debt.project.team.members)
    is_lead = (current_user.role == UserRole.lead and debt.project.team.lead_id == current_user.id)

    if not (is_admin or is_team_member or is_lead):
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to comment on this technical debt. Only project team members, leads, or admins can comment."
        )

    # 3. Create Comment
    comment = DebtComment(
        debt_id=debt_id,
        user_id=current_user.id,
        comment=sanitize_text(data.comment)
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

@router.get("/{debt_id}/comments", response_model=list[DebtCommentResponse])
def get_debt_comments(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    debt = db.query(TechnicalDebt).filter(TechnicalDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Technical Debt not found")

    is_admin = current_user.role == UserRole.admin
    is_team_member = any(m.id == current_user.id for m in debt.project.team.members)
    
    if not (is_admin or is_team_member):
        raise HTTPException(status_code=403, detail="Not authorized to view comments.")

    return db.query(DebtComment).options(
        joinedload(DebtComment.user) 
    ).filter(
        DebtComment.debt_id == debt_id
    ).order_by(DebtComment.created_at.desc()).all()



@router.delete("/comments/{comment_id}")
def delete_debt_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = db.query(DebtComment).filter(DebtComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    debt = db.query(TechnicalDebt).filter(TechnicalDebt.id == comment.debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Technical Debt not found")

    is_admin = current_user.role == UserRole.admin
    is_author = comment.user_id == current_user.id  
    is_team_lead = (current_user.role == UserRole.lead and debt.project.team.lead_id == current_user.id)

    if not (is_admin or is_author or is_team_lead):
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to delete this comment only the author / team lead or admin can delete it"
        )

    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted successfully"}

@router.put("/comments/{comment_id}", response_model=DebtCommentResponse)   
def update_debt_comment(
    comment_id: int,
    data: DebtCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = db.query(DebtComment).filter(DebtComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    debt = db.query(TechnicalDebt).filter(TechnicalDebt.id == comment.debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Technical Debt not found")

    is_admin = current_user.role == UserRole.admin
    is_author = comment.user_id == current_user.id  
    is_team_lead = (current_user.role == UserRole.lead and debt.project.team.lead_id == current_user.id)

    if not (is_admin or is_author or is_team_lead):
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to update this comment only the author / team lead or admin can update it"
        )

    comment.comment = sanitize_text(data.comment)
    db.commit()
    db.refresh(comment)
    return comment
