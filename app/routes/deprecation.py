
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Deprecation, Project
from app.schemas.dependencies import get_current_user, deprecationsCreate, deprecationsUpdate

router = APIRouter(
    prefix="/deprecations",
    tags=["Deprecations"]
)


@router.post("/deprecation")
def create_deprecation(deprecation:deprecationsCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    project = db.query(Project).filter(Project.id == deprecation.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with id {deprecation.project_id} not found")
        
    dep=Deprecation(**deprecation.dict())
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

@router.put("/deprecation/{id}")
def update_deprecation(id:int,deprecation:deprecationsUpdate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    dep=db.query(Deprecation).filter(Deprecation.id==id).first()
    if not dep:
        raise HTTPException(status_code=404,detail="Deprecation not found")
    for key,value in deprecation.dict(exclude_unset=True).items():
        setattr(dep,key,value)
    db.commit()
    db.refresh(dep)
    return dep

@router.delete("/deprecation/{id}")
def delete_deprecation(id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    dep=db.query(Deprecation).filter(Deprecation.id==id).first()
    if not dep:
        raise HTTPException(status_code=404,detail="Deprecation not found")
    db.delete(dep)
    db.commit()
    return {"message":"Deprecation deleted successfully"}
