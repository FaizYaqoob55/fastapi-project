
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy.orm import Query, Session, joinedload
from app.database import get_db
from datetime import date, timedelta
from app.models import User, Deprecation, Project, DeprecationTimeline, TechnicalDebt
from app.schemas.dependencies import (
    get_current_user, 
    deprecationsCreate, 
    deprecationsUpdate, 
    deprecationsResponse,
    DeprecationTimelineResponse,
    ImpactReport,
    UserRole
)
from app.model.role import TimeLineStage
from app.utils.security import sanitize_text
from typing import Literal

router = APIRouter(
    prefix="/deprecations",
    tags=["Deprecations"]
)


def calculate_impact(users_count:int)->str:
    if users_count>5000:
        return "HIGH"
    elif users_count>500:
        return "MEDIUM"
    else:
        return "LOW"


@router.post("/deprecation")
def create_deprecation(deprecation:deprecationsCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    project = db.query(Project).filter(Project.id == deprecation.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with id {deprecation.project_id} not found")
    
    is_admin = current_user.role == UserRole.admin
    is_team_lead = (current_user.role == UserRole.lead and project.team.lead_id == current_user.id)
    is_member = any(m.id == current_user.id for m in project.team.members)

    if not (is_admin or is_team_lead or is_member):
        raise HTTPException(
            status_code=403, 
            detail="Aap is project ke liye deprecation notice create nahi kar sakte."
        )

    impact=calculate_impact(deprecation.affected_users_count or 0)
    dep_data = deprecation.dict()
    dep_data['impact_level'] = impact
    if 'affected_systems' in dep_data:
        dep_data['affected_system'] = dep_data.pop('affected_systems')
    dep_data['migration_notes'] = sanitize_text(dep_data['migration_notes'])
    dep_data['item_name'] = sanitize_text(dep_data['item_name'])
    dep_data['replacement'] = sanitize_text(dep_data['replacement'])
    dep_data['current_version'] = sanitize_text(dep_data['current_version'])
    dep_data['deprecated_in'] = sanitize_text(dep_data['deprecated_in'])
    dep_data['removal_planned_for'] = sanitize_text(dep_data['removal_planned_for'])
    dep=Deprecation(**dep_data)
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep

@router.get("/deprecation", response_model=list[deprecationsResponse])
def list_deprecations(
    project_id: int | None = None,
    type: str | None = None,
    impact_level: str | None = None,
    search: str | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Base Query with Eager Loading
    query = db.query(Deprecation).options(
        joinedload(Deprecation.project),
        joinedload(Deprecation.timeline),
        joinedload(Deprecation.technical_debts)
    )
    
    if current_user.role != UserRole.admin:
        user_team_ids = [t.id for t in current_user.teams] 
        
        allowed_projects_subquery = db.query(Project.id).filter(Project.team_id.in_(user_team_ids))
        
        query = query.filter(Deprecation.project_id.in_(allowed_projects_subquery))
    
    # 3. Filters
    if project_id:
        query = query.filter(Deprecation.project_id == project_id)
    if type:
        query = query.filter(Deprecation.type == type)
    if impact_level:
        query = query.filter(Deprecation.impact_level == impact_level)
    if search:
        query = query.filter(Deprecation.item_name.ilike(f"%{search}%"))
        
    # 4. Sorting Logic
    allowed_sort_fields = {
        "project_id": Deprecation.project_id,
        "type": Deprecation.type,
        "impact_level": Deprecation.impact_level,
        "name": Deprecation.item_name,
        "date": Deprecation.created_at
    }
    
    sort_column = allowed_sort_fields.get(sort_by, Deprecation.created_at)
    if order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    return query.all()

@router.get("/{id}", response_model=deprecationsResponse) 
def get_deprecation(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    dep = db.query(Deprecation).options(
        joinedload(Deprecation.project),
        joinedload(Deprecation.timeline),
        joinedload(Deprecation.technical_debts)
    ).filter(Deprecation.id == id).first()

    if not dep:
        raise HTTPException(status_code=404, detail="Deprecation notice not found.")

    if current_user.role != UserRole.admin:
        user_team_ids = [t.id for t in current_user.teams]
        
        if dep.project.team_id not in user_team_ids:
            raise HTTPException(
                status_code=403, 
                detail="You are not authorized to view this deprecation notice."
            )

    return dep

@router.get("/upcoming-deadlines", response_model=list[DeprecationTimelineResponse])
def upcoming_deadlines(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    next_30_days = today + timedelta(days=30)
    query = db.query(DeprecationTimeline).join(Deprecation).join(Project)
    query = query.filter(
        DeprecationTimeline.planned_date >= today, 
        DeprecationTimeline.planned_date <= next_30_days
    )
    if current_user.role != UserRole.admin:
        user_team_ids = [t.id for t in current_user.teams]
        query = query.filter(Project.team_id.in_(user_team_ids))
    return query.order_by(DeprecationTimeline.planned_date.asc()).all()


@router.put("/deprecation/{id}")
def update_deprecation(id:int,deprecation:deprecationsUpdate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    dep=db.query(Deprecation).filter(Deprecation.id==id).first()
    if not dep:
        raise HTTPException(status_code=404,detail="Deprecation not found")
    if current_user.role != UserRole.admin and dep.project_id not in (
        db.query(Project.id).filter(Project.team_id == current_user.team_id).all()
    ):
        raise HTTPException(status_code=403,detail="Not authorized to update this deprecation")
    for key,value in deprecation.dict(exclude_unset=True).items():
        setattr(dep,key,value)
    impact=calculate_impact(deprecation.affected_users_count or 0)
    dep.impact_level=impact
    dep.migration_notes = sanitize_text(dep.migration_notes)
    dep.item_name = sanitize_text(dep.item_name)
    dep.replacement = sanitize_text(dep.replacement)
    dep.current_version = sanitize_text(dep.current_version)
    dep.deprecated_in = sanitize_text(dep.deprecated_in)
    dep.removal_planned_for = sanitize_text(dep.removal_planned_for)
    db.commit()
    db.refresh(dep)
    return dep


@router.post("/{id}/link-debt/{debt_id}")
def link_debt(
    id: int, 
    debt_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # 1. Fetch Deprecation with Project Info
    dep = db.query(Deprecation).filter(Deprecation.id == id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Deprecation notice not found.")

    # 2. RBAC: Team Access Check
    user_team_ids = [t.id for t in current_user.teams]
    if current_user.role != UserRole.admin and dep.project.team_id not in user_team_ids:
        raise HTTPException(status_code=403, detail="You are not authorized to link debt to this deprecation.")

    debt = db.query(TechnicalDebt).filter(TechnicalDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Technical Debt not found.")

    if dep.project_id != debt.project_id:
        raise HTTPException(
            status_code=400, 
            detail="You can only link debt to the same project's deprecation."
        )

    # 4. Check for Duplicate Link
    if debt in dep.technical_debts:
        return {"message": "Debt is already linked to this deprecation."}

    dep.technical_debts.append(debt)
    db.commit()
    
    return {"message": f"Debt '{debt.title}' ko deprecation '{dep.item_name}' se link kar diya gaya hai."}
@router.get("/{id}/impact-report", response_model=ImpactReport)
def impact_report(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dep = db.query(Deprecation).options(
        joinedload(Deprecation.project),
        joinedload(Deprecation.timeline),
        joinedload(Deprecation.technical_debts)
    ).filter(Deprecation.id == id).first()
    
    if not dep:
        raise HTTPException(status_code=404, detail="Deprecation not found")

    # 2. Optimized RBAC Check
    if current_user.role != UserRole.admin:
        # Check if user belongs to the team that owns the project
        user_team_ids = [t.id for t in current_user.teams]
        if dep.project.team_id not in user_team_ids:
            raise HTTPException(status_code=403, detail="You are not authorized to view the impact report for this deprecation.")

    today = date.today()
    upcoming = [
        t for t in dep.timeline 
        if t.planned_date >= today and t.stage != TimeLineStage.removed
    ]

    return ImpactReport(
        item_name=dep.item_name,
        impact_level=dep.impact_level or "LOW",
        affected_users_count=dep.affected_users_count or 0,
        affected_system=dep.affected_system or "None",
        upcoming_milestones=upcoming,
        linked_debt_count=len(dep.technical_debts)
    )

@router.delete("/{id}") 
def delete_deprecation(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dep = db.query(Deprecation).filter(Deprecation.id == id).first()
    
    if not dep:
        raise HTTPException(status_code=404, detail="Deprecation not found")

    is_admin = current_user.role == UserRole.admin
    is_lead = (current_user.role == UserRole.lead and dep.project.team.lead_id == current_user.id)

    if not (is_admin or is_lead):
        raise HTTPException(status_code=403, detail="only admins or team leads can delete deprecations")
    db.delete(dep)
    db.commit()
    return {"message": "Deprecation deleted successfully"}