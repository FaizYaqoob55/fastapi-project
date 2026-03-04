
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from datetime import date, timedelta
from app.models import User, Deprecation, Project, DeprecationTimeline, TechnicalDebt
from app.schemas.dependencies import (
    get_current_user, 
    deprecationsCreate, 
    deprecationsUpdate, 
    DeprecationTimelineResponse,
    ImpactReport
)
from app.model.role import TimeLineStage


router = APIRouter(
    prefix="/deprecations",
    tags=["Deprecations"]
)


def calculate_impact(users_count:int)->str:
    if users_count>10000:
        return "HIGH"
    elif users_count>1000:
        return "MEDIUM"
    else:
        return "LOW"


@router.post("/deprecation")
def create_deprecation(deprecation:deprecationsCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    project = db.query(Project).filter(Project.id == deprecation.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with id {deprecation.project_id} not found")
    impact=calculate_impact(deprecation.affected_users_count or 0)
    dep_data = deprecation.dict()
    dep_data['impact_level'] = impact
    if 'affected_systems' in dep_data:
        dep_data['affected_system'] = dep_data.pop('affected_systems')
    dep=Deprecation(**dep_data)
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep

@router.get("/deprecation")
def list_deprecations(
    project_id:int |None=None,
    type:str |None=None,
    impact_level:int |None=None,
    search:str |None=None,
    sort_by:str |None=None,
    db:Session=Depends(get_db)
):
    query=db.query(Deprecation)
    if project_id:
        query=query.filter(Deprecation.project_id==project_id)
    if type:
        query=query.filter(Deprecation.type==type)
    if impact_level:
        query=query.filter(Deprecation.impact_level==impact_level)
    if search:
        query=query.filter(Deprecation.item_name.ilike(f"%{search}%"))
    if sort_by:
        if sort_by=="project_id":
            query=query.order_by(Deprecation.project_id)
        elif sort_by=="type":
            query=query.order_by(Deprecation.type)
        elif sort_by=="impact_level":
            query=query.order_by(Deprecation.impact_level)
        elif sort_by=="search":
            query=query.order_by(Deprecation.item_name)
    return query.all()


@router.get("/deprecation/{id}")
def get_deprecation(id:int,db:Session=Depends(get_db)):
    dep=db.query(Deprecation).filter(Deprecation.id==id).first()
    if not dep:
        raise HTTPException(status_code=404,detail="Deprecation not found")
    return dep


@router.get("/upcoming-deadlines",response_model=list[DeprecationTimelineResponse])
def upcoming_deadlines(db:Session=Depends(get_db)):
    today=date.today()
    next_30_days=today+timedelta(days=30)
    results=db.query(DeprecationTimeline).filter(DeprecationTimeline.planned_date>=today, DeprecationTimeline.planned_date<=next_30_days).all()
    return results


@router.put("/deprecation/{id}")
def update_deprecation(id:int,deprecation:deprecationsUpdate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    dep=db.query(Deprecation).filter(Deprecation.id==id).first()
    if not dep:
        raise HTTPException(status_code=404,detail="Deprecation not found")
    for key,value in deprecation.dict(exclude_unset=True).items():
        setattr(dep,key,value)
    impact=calculate_impact(deprecation.affected_users_count or 0)
    dep.impact_level=impact
    db.commit()
    db.refresh(dep)
    return dep


@router.post("/{id}/link-debt/{debt_id}")
def link_debt(id:int,debt_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    dep=db.query(Deprecation).filter(Deprecation.id==id).first()
    if not dep:
        raise HTTPException(status_code=404,detail="Deprecation not found")
    debt=db.query(TechnicalDebt).filter(TechnicalDebt.id==debt_id).first()
    if not debt:
        raise HTTPException(status_code=404,detail="Debt not found")
    dep.technical_debts.append(debt)
    db.commit()
    db.refresh(dep)
    return {"message":"Debt linked successfully"}

@router.get("/{id}/impact-report",response_model=ImpactReport)
def impact_report(id:int,db:Session=Depends(get_db)):
    dep=db.query(Deprecation).filter(Deprecation.id==id).first()
    if not dep:
        raise HTTPException(status_code=404,detail="Deprecation not found")
    today = date.today()
    upcoming=[
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



@router.delete("/deprecation/{id}")
def delete_deprecation(id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    dep=db.query(Deprecation).filter(Deprecation.id==id).first()
    if not dep:
        raise HTTPException(status_code=404,detail="Deprecation not found")
    db.delete(dep)
    db.commit()
    return {"message":"Deprecation deleted successfully"}
