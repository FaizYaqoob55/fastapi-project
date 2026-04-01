import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session,joinedload
from sqlalchemy import asc, desc, or_
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




@router.post("/", response_model=TechnicalResponse)
@limiter.limit("5/minute")
def create_technical_debt(
    request: Request,
    data: TechnicalDebtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
): 
    # 1. Project Check & Authorization
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    is_member = any(m.id == current_user.id for m in project.team.members)
    if current_user.role != UserRole.admin and project.team.lead_id != current_user.id and not is_member:
        raise HTTPException(status_code=403, detail="Not authorized to create technical debt for this project")

    target_owner_id = data.owner_id or current_user.id
    
    if target_owner_id != current_user.id:
        owner = db.query(User).filter(User.id == target_owner_id).first()
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")
        
        if current_user.role != UserRole.admin and project.team.lead_id != current_user.id:
            raise HTTPException(status_code=403, detail="ONLY ADMIN OR TEAM LEAD CAN ASSIGN TECHNICAL DEBT TO OTHERS.")

    # 3. Creation
    debt = TechnicalDebt(
        project_id=data.project_id,
        owner_id=target_owner_id,
        title=sanitize_text(data.title),
        description=sanitize_text(data.description),
        priority=data.priority,
        severity=data.severity,
        estimated_effort=data.estimated_effort,
        due_date=data.due_date,
        status="open" 
    )
    
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return debt



@router.get("/", response_model=list[TechnicalResponse])
def get_technical_debts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_id: Optional[int] = Query(None),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None), 
    sort_by: Optional[str] = Query("created_at", description="priority | due_date | created_at"),
    order: Optional[str] = Query("desc", description="asc | desc")
):
    query = db.query(TechnicalDebt).options(
        joinedload(TechnicalDebt.owner),
        joinedload(TechnicalDebt.project)
    )

    if current_user.role != UserRole.admin:
        user_team_ids = [t.id for t in current_user.teams] # Assuming relationship is 'teams'
        
        allowed_projects_subquery = db.query(Project.id).filter(Project.team_id.in_(user_team_ids))
        
        query = query.filter(TechnicalDebt.project_id.in_(allowed_projects_subquery))
        
        if current_user.role == UserRole.member:
             query = query.filter(TechnicalDebt.owner_id == current_user.id)

    # --- Filters ---
    if project_id:
        query = query.filter(TechnicalDebt.project_id == project_id)
    if priority:
        query = query.filter(TechnicalDebt.priority == priority)
    if status:
        query = query.filter(TechnicalDebt.status == status)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                TechnicalDebt.title.ilike(search_filter),
                TechnicalDebt.description.ilike(search_filter)
            )
        )

    # --- Sorting Logic ---
    allowed_fields = {
        "priority": TechnicalDebt.priority,
        "due_date": TechnicalDebt.due_date,
        "created_at": TechnicalDebt.created_at
    }
    
    sort_column = allowed_fields.get(sort_by, TechnicalDebt.created_at)
    if order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    return query.all()




@router.get("/technical-debt", response_model=list[TechnicalResponse])
@limiter.limit("5/minute")
def get_technical_debt_list(
    request: Request,
    skip: int = 0, 
    limit: int = 10, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
): 
    query = db.query(TechnicalDebt).options(
        joinedload(TechnicalDebt.owner),
        joinedload(TechnicalDebt.project)
    )

    if current_user.role != UserRole.admin:
        # User ki apni team ke projects ki subquery
        user_team_ids = [t.id for t in current_user.teams]
        allowed_projects = db.query(Project.id).filter(Project.team_id.in_(user_team_ids))
        
        query = query.filter(TechnicalDebt.project_id.in_(allowed_projects))

    return query.offset(skip).limit(limit).all()

@router.get("/{debt_id}", response_model=TechnicalResponse)
def get_technical_debt(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    debt = db.query(TechnicalDebt).options(
        joinedload(TechnicalDebt.owner),
        joinedload(TechnicalDebt.project)
    ).filter(TechnicalDebt.id == debt_id).first()

    if not debt:
        raise HTTPException(status_code=404, detail="Technical Debt not found")

   
    is_admin = current_user.role == UserRole.admin
    is_owner = debt.owner_id == current_user.id
    is_team_member = any(t.id == debt.project.team_id for t in current_user.teams)

    if not (is_admin or is_owner or is_team_member):
        raise HTTPException(status_code=403, detail="Not authorized to view this technical debt")
        
    return debt
 
@router.put("/{debt_id}", response_model=TechnicalResponse)
def update_technical_debt(
    debt_id: int,
    data: TechnicalDebtUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch debt with project/team info
    debt = db.query(TechnicalDebt).filter(TechnicalDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Technical debt not found")

    # 2. Advanced RBAC Check
    is_admin = current_user.role == UserRole.admin
    is_owner = debt.owner_id == current_user.id
    # Check if current_user is the Lead of the team this project belongs to
    is_team_lead = (current_user.role == UserRole.lead and debt.project.team.lead_id == current_user.id)

    if not (is_admin or is_owner or is_team_lead):
        raise HTTPException(status_code=403, detail="Not authorized to update this technical debt. Only the owner, team lead, or admin can update it.")

    # 3. Dynamic Update
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(debt, key, value)

    # 4. Sanitization & Finalization
    debt.title = sanitize_text(debt.title)
    debt.description = sanitize_text(debt.description)
    
    db.commit()
    db.refresh(debt)
    return debt

@router.delete("/{debt_id}")
def delete_technical_debt(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    debt = db.query(TechnicalDebt).filter(TechnicalDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Technical Debt not found")

    # Same Advanced RBAC for Delete
    is_admin = current_user.role == UserRole.admin
    is_owner = debt.owner_id == current_user.id
    is_team_lead = (current_user.role == UserRole.lead and debt.project.team.lead_id == current_user.id)

    if not (is_admin or is_owner or is_team_lead):
        raise HTTPException(status_code=403, detail="Not authorized to delete this technical debt")

    db.delete(debt)
    db.commit()
    return {"message": "Technical Debt deleted successfully"}





@router.patch("/{debt_id}/priority")
def update_debt_priority(debt_id:int,data:PriorityUpdate,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)
                         ):
    debt=db.query(TechnicalDebt).filter(TechnicalDebt.id==debt_id).first()
    if not debt:
        raise HTTPException(status_code=404,detail="Debt not found")
    is_admin = current_user.role == UserRole.admin
    is_owner = debt.owner_id == current_user.id
    is_team_lead = (current_user.role == UserRole.lead and debt.project.team.lead_id == current_user.id)

    if not (is_admin or is_owner or is_team_lead):
        raise HTTPException(status_code=403, detail="Not authorized to update this technical debt's priority. Only the owner, team lead, or admin can update it.")

    debt.priority=data.priority
    db.commit()
    return {"message":"Debt priority updated"}

@router.patch("/{debt_id}/status")
def update_debt_status(
    debt_id: int,
    status: DebtStatus = Body(..., embed=True),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch debt with project/team info for RBAC
    debt = db.query(TechnicalDebt).filter(TechnicalDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Technical debt not found")

    # 2. Advanced RBAC (Admin, Owner, or Team Lead)
    is_admin = current_user.role == UserRole.admin
    is_owner = debt.owner_id == current_user.id
    is_team_lead = (current_user.role == UserRole.lead and debt.project.team.lead_id == current_user.id)

    if not (is_admin or is_owner or is_team_lead):
        raise HTTPException(status_code=403, detail="Not authorized to update this technical debt's status. Only the owner, team lead, or admin can update it.")

    # 3. Optimization: Agar status same hai to database hit na karein
    if debt.status == status:
        return {"message": "Status is already set to " + status}

    # 4. Create History Entry
    status_history = DebtStatusHistory(
        technical_debt_id=debt.id,
        old_status=debt.status,
        new_status=status,
        changed_by=current_user.id,
        changed_at=datetime.utcnow() 
    )

    # 5. Update Debt & Save
    debt.status = status
    db.add(status_history)
    db.commit()
    
    return {
        "message": f"Debt status updated from {status_history.old_status} to {status}"
    }





@router.get("/{debt_id}/history")
def get_status_history(
    debt_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    debt = db.query(TechnicalDebt).filter(TechnicalDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Technical Debt not found")
    is_admin = current_user.role == UserRole.admin
    is_owner = debt.owner_id == current_user.id
    is_team_lead = (current_user.role == UserRole.lead and debt.project.team.lead_id == current_user.id)

    if not (is_admin or is_owner or is_team_lead):
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to view this technical debt's status history. Only the owner, team lead, or admin can view it."
        )
    
    return db.query(DebtStatusHistory).options(
        joinedload(DebtStatusHistory.user)
    ).filter(
        DebtStatusHistory.technical_debt_id == debt_id
    ).order_by(DebtStatusHistory.changed_at.desc()).all()



@router.patch("/{debt_id}/assign")
def assign_technical_debt_owner(
    debt_id: int,
    owner_id: int = Body(..., embed=True),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    debt = db.query(TechnicalDebt).filter(TechnicalDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Technical Debt not found")

    is_admin = current_user.role == UserRole.admin
    is_team_lead = (current_user.role == UserRole.lead and debt.project.team.lead_id == current_user.id)

    if not (is_admin or is_team_lead):
        raise HTTPException(status_code=403, detail="Not authorized to assign this technical debt. Only the team lead or admin can assign it.")

    owner = db.query(User).filter(User.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Assignee (New Owner) not found")

    debt.owner_id = owner_id
    db.commit()
    
    return {"message": f"Technical debt successfully assigned to {owner.name or owner.email}"}