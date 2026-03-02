from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User,Deprecation,DeprecationTimeline
from app.schemas.dependencies import get_current_user,DeprecationTimelineCreate


router = APIRouter(
    prefix="/deprecation_timeline",
    tags=["Deprecation Timeline"]
)



@router.post("/deprecations/{deprecation_id}/timeline")
def create_deprecation_timeline(deprecation_id:int, timeline:DeprecationTimelineCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    deprecation = db.query(Deprecation).filter(Deprecation.id == deprecation_id).first()
    if not deprecation:
        raise HTTPException(status_code=404,detail="Deprecation not found")
    timeline = DeprecationTimeline(deprecation_id=deprecation_id,stage=data.stage,planned_date=data.planned_date)

    db.add(timeline)
    db.commit()
    db.refresh(timeline)
    return timeline

@router.get("/deprecations/{deprecation_id}/timeline")
def get_deprecation_timeline(deprecation_id:int,db:Session=Depends(get_db)):
    timeline = db.query(DeprecationTimeline).filter(DeprecationTimeline.deprecation_id == deprecation_id).all()
    if not timeline:
        raise HTTPException(status_code=404,detail="Timeline not found")
    return timeline



@router.put("/deprecations/{deprecation_id}/timeline/{timeline_id}")
def update_deprecation_timeline(deprecation_id:int,timeline_id:int,timeline:DeprecationTimelineCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    deprecation = db.query(Deprecation).filter(Deprecation.id == deprecation_id).first()
    if not deprecation:
        raise HTTPException(status_code=404,detail="Deprecation not found")
    timeline = db.query(DeprecationTimeline).filter(DeprecationTimeline.id == timeline_id).first()
    if not timeline:
        raise HTTPException(status_code=404,detail="Timeline not found")
    timeline.stage = timeline.stage
    timeline.planned_date = timeline.planned_date
    db.commit()
    db.refresh(timeline)
    return timeline

@router.delete("/deprecations/{deprecation_id}/timeline/{timeline_id}")
def delete_deprecation_timeline(deprecation_id:int,timeline_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    deprecation = db.query(Deprecation).filter(Deprecation.id == deprecation_id).first()
    if not deprecation:
        raise HTTPException(status_code=404,detail="Deprecation not found")
    timeline = db.query(DeprecationTimeline).filter(DeprecationTimeline.id == timeline_id).first()
    if not timeline:
        raise HTTPException(status_code=404,detail="Timeline not found")
    db.delete(timeline)
    db.commit()
    return {"message":"Timeline deleted successfully"}
