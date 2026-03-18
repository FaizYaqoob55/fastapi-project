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
    prefix="/technical-debts",
    tags=["Technical Debt"]
)




@router.post("/",response_model=TechnicalResponse)
@limiter.limit("5/minute")
def create_technical_debt(request: Request,data:TechnicalDebtCreate,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
): 
    if owner_id := data.owner_id:
        owner = db.query(User).filter(User.id == owner_id).first()
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")
        if current_user.role != UserRole.admin and owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to assign technical debt to this user")
    if not (project := db.query(Project).filter(Project.id == data.project_id).first()):
        raise HTTPException(status_code=404, detail="Project not found")
    # ensure owner_id is valid; default to current user

    owner_id = data.owner_id or current_user.id
    debt=TechnicalDebt(
        project_id=data.project_id,
        owner_id=owner_id,
        title=sanitize_text(data.title),
        description=sanitize_text(data.description),
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
    db:Session=Depends(get_db),current_user=Depends(get_current_user),
    project_id:Optional[int]=Query(None),
    priority:Optional[str]=Query(None),
    status:Optional[str]=Query(None),
    search:Optional[str]=Query(None), 
    sort_by:Optional[str]=Query(None,description="priority | due_date | created_at"),
    order:Optional[str]=Query("desc",description="asc | desc")

):
    query=db.query(TechnicalDebt).options(
        joinedload(TechnicalDebt.owner),
        joinedload(TechnicalDebt.project)
    )
    if current_user.role == UserRole.admin:
        pass  # Admins can see all technical debts
    elif current_user.role == UserRole.lead:
        # Leads can see all debts associated with their teams
        team_ids = [t.id for t in current_user.team] if current_user.team else []
        query=query.filter(TechnicalDebt.project_id.in_(
            db.query(Project.id).filter(Project.team_id.in_(team_ids)).all()
        ))
    else:
        # Developers/Viewers can only see debts assigned to them, within their teams
        query=query.filter(TechnicalDebt.owner_id == current_user.id)
        team_ids = [t.id for t in current_user.team] if current_user.team else []
        query=query.filter(TechnicalDebt.project_id.in_(
            db.query(Project.id).filter(Project.team_id.in_(team_ids)).all()
        ))
    
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





@router.get("/technical-debt")
@limiter.limit("5/minute")
def get_technical_debt_list(
    request: Request,
    Skip:int=0,
    limit:int=1,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
): 
    return db.query(TechnicalDebt).options(
        joinedload(TechnicalDebt.owner),
        joinedload(TechnicalDebt.project)
    ).offset(Skip).limit(limit).all()

@router.get("/{debt_id}",response_model=TechnicalResponse)
def get_technical_debt(
    debt_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    debt=db.query(TechnicalDebt).options(
        joinedload(TechnicalDebt.owner),
        joinedload(TechnicalDebt.project)
    ).filter(TechnicalDebt.id==debt_id).first()
    if not debt:
        raise HTTPException(status_code=404,detail="Technical Debt not found")
    if current_user.role != UserRole.admin and debt.owner_id != current_user.id:
        raise HTTPException(status_code=403,detail="Not authorized to view this technical debt")
    return debt
 
@router.put("/{debt_id}",response_model=TechnicalResponse)
def update_technical_debt(
    debt_id:int,
    data:TechnicalDebtUpdate,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    debt=db.query(TechnicalDebt).filter(TechnicalDebt.id==debt_id).first()
    if not debt:
        raise HTTPException(status_code=404,detail="Technical debt not found")
    if current_user.role != UserRole.admin and debt.owner_id != current_user.id:
        raise HTTPException(status_code=403,detail="Not authorized to update this technical debt")
    for key,value in data.dict(exclude_unset=True).items():
        setattr(debt,key,value)

    debt.title=sanitize_text(debt.title)
    debt.description=sanitize_text(debt.description)
    
    db.commit()
    db.refresh(debt)
    return debt



@router.delete("/{debt_id}")
def delete_technical_debt(
    debt_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    debt=db.query(TechnicalDebt).filter(TechnicalDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404,detail="Technical Debt not found")
    if current_user.role != UserRole.admin and debt.owner_id != current_user.id:
        raise HTTPException(status_code=403,detail="Not authorized to delete this technical debt")
    db.delete(debt)
    db.commit()
    return {"message":"Technical Debt deleted"}    






@router.patch("/{debt_id}/priority")
def update_debt_priority(debt_id:int,data:PriorityUpdate,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)
                         ):
    debt=db.query(TechnicalDebt).filter(TechnicalDebt.id==debt_id).first()
    if not debt:
        raise HTTPException(status_code=404,detail="Debt not found")
    if current_user.role != UserRole.admin and debt.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this technical debt")
    
    debt.priority=data.priority
    db.commit()
    return {"message":"Debt priority updated"}

@router.patch("/{debt_id}/status")
def update_debt_status(debt_id:int,
                       status:DebtStatus=Body(...,embed=True),
                       db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        debt=db.query(TechnicalDebt).filter(TechnicalDebt.id==debt_id).first()
        if not debt:
            raise HTTPException(status_code=404,detail="technical debt not found")
        if current_user.role != UserRole.admin and debt.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this technical debt")
        
        statushistory=DebtStatusHistory(
            technical_debt_id=debt.id,
            old_status=debt.status,
            new_status=status,
            changed_by=current_user.id
        )

        debt.status=status
        db.add(statushistory)
        db.commit()
        return {"message":"Debt status updated"}
    



@router.get("/{debt_id}/history")
def get_status_history(debt_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    debt=db.query(TechnicalDebt).filter(TechnicalDebt.id==debt_id).first()
    if not debt:
        raise HTTPException(status_code=404,detail="Technical Debt not found")
    if current_user.role != UserRole.admin and debt.owner_id != current_user.id:
        raise HTTPException(status_code=403,detail="Not authorized to view this technical debt history")
    return db.query(DebtStatusHistory).filter(
        DebtStatusHistory.technical_debt_id==debt_id
    ).order_by(DebtStatusHistory.changed_at.desc()).all()





@router.patch("/{debt_id}/assign")
def assign_technical_debt_owner(debt_id:int,
                                owner_id:int=Body(...,embed=True),
                                db:Session=Depends(get_db),
                                current_user:User=Depends(get_current_user)):
    debt=db.query(TechnicalDebt).filter(TechnicalDebt.id==debt_id).first()
    if not debt:
        raise HTTPException(status_code=404,detail="Technical Debt not found")
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403,detail="Not authorized to assign technical debt")
    owner=db.query(User).filter(User.id==owner_id).first()
    if not owner:
        raise HTTPException(status_code=404,detail="Owner not found")
    debt.owner_id=owner_id
    db.commit()
    return {"message":f"Technical debt assigned to {owner.email}"}