from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from app.database import get_db
from app.schemas.dependencies import (
    get_current_user, 
    TechnicalResponse,
    TechnicalDebtCreate,
    TechnicalDebtUpdate,
    DebtCommentCreate,
    DebtCommentResponse
)
from app.models import TechnicalDebt, User, DebtComment


router = APIRouter(
    prefix="/technical-debts",
    tags=["Technical Debt"]
)




@router.post("/",response_model=TechnicalResponse)
def create_technical_debt(
    data:TechnicalDebtCreate,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    debt=TechnicalDebt(
        project_id=data.project_id,
        owner_id=data.owner_id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        severity=data.severity,
        estimated_effort=data.estimated_effort,
        due_date=data.due_date
    )
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return debt 




@router.get("/",response_model=list[TechnicalResponse])
def get_technical_debts(
    db:Session=Depends(get_db),
    project_id:Optional[int]=Query(None),
    priority:Optional[str]=Query(None),
    status:Optional[str]=Query(None),
    search:Optional[str]=Query(None), 
    sort_by:Optional[str]=Query(None,description="priority | due_date | created_at"),
    order:Optional[str]=Query("desc",description="asc | desc")

):
    query=db.query(TechnicalDebt)
    #    filters
    if project_id:
        query=query.filter(TechnicalDebt.project_id == project_id)
    if priority:
        query=query.filter(TechnicalDebt.priority == priority)
    if status:
        query=query.filter(TechnicalDebt.status == status)
    if search:
        query=query.filter(
            TechnicalDebt.title.ilike(f"%{search}%") |
            TechnicalDebt.description.ilike(f"%{search}%")
        )


    #   sorting 

    sort_column = None
    if sort_by:
        allowed_fields={"priority":TechnicalDebt.priority,"due_date":TechnicalDebt.due_date,"created_at":TechnicalDebt.created_at}
        sort_column=allowed_fields.get(sort_by)
        if not sort_column:
            raise HTTPException(status_code=400,detail="Invalid sort_by field")
        if order == "asc":
            query=query.order_by(asc(sort_column))
        else:
            query=query.order_by(desc(sort_column))

    return query.all()





@router.get("/{debt_id}",response_model=TechnicalResponse)
def get_technical_debt(
    debt_id:int,
    db:Session=Depends(get_db)
):
    debt=db.query(TechnicalDebt).filter(TechnicalDebt.id==debt_id).first()
    if not debt:
        raise HTTPException(status_code=404,detail="Technical Debt not found")
    return debt

@router.put("/{debt_id}",response_model=TechnicalResponse)
def update_technical_debt(
    debt_id:int,
    data:TechnicalDebtUpdate,
    db:Session=Depends(get_db)
):
    debt=db.query(TechnicalDebt).filter(TechnicalDebt.id==debt_id).first()
    if not debt:
        raise HTTPException(status_code=404,detail="Technical debt not found")
    for key,value in data.dict(exclude_unset=True).items():
        setattr(debt,key,value)
    db.commit()
    db.refresh(debt)
    return debt


@router.delete("/{debt_id}")
def delete_technical_debt(
    debt_id:int,
    db:Session=Depends(get_db)
):
    debt=db.query(TechnicalDebt).filter(TechnicalDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404,detail="Technical Debt not found")

    db.delete(debt)
    db.commit()
    return {"message":"Technical Debt deleted"}    



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

    comment = DebtComment(
        debt_id=debt_id,
        user_id=current_user.id,
        comment=data.comment
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
    db: Session = Depends(get_db)
):
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
        raise HTTPException(404, "Comment not found")

    if comment.user_id != current_user.id:
        raise HTTPException(403, "Not allowed")

    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}