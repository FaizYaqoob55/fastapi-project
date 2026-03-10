from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User,Deprecation,DeprecationTimeline
from app.schemas.dependencies import get_current_user,DeprecationTimelineCreate
from app.model.role import TimeLineStage
from app.utils.security import sanitize_text


router = APIRouter(
    prefix="/deprecation_timeline",
    tags=["Deprecation Timeline"]
)



@router.post("/deprecations/{deprecation_id}/timeline")
def create_deprecation_timeline(deprecation_id:int, timeline:DeprecationTimelineCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    deprecation = db.query(Deprecation).filter(Deprecation.id == deprecation_id).first()
    if not deprecation:
        raise HTTPException(status_code=404,detail="Deprecation not found")
    timeline = DeprecationTimeline(deprecation_id=deprecation_id,stage=timeline.stage,planned_date=timeline.planned_date,notes=sanitize_text(timeline.notes))
    existing_timeline = db.query(DeprecationTimeline).filter(DeprecationTimeline.deprecation_id == deprecation_id,DeprecationTimeline.stage == timeline.stage).first()
    if existing_timeline:
        raise HTTPException(status_code=400,detail="Timeline already exists")


   

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
    timeline_obj = db.query(DeprecationTimeline).filter(DeprecationTimeline.id == timeline_id).first()
    if not timeline_obj:
        raise HTTPException(status_code=404,detail="Timeline not found")
    if timeline_obj.stage == TimeLineStage.removed:
        raise HTTPException(status_code=400,detail="Timeline already removed")
    timeline_obj.stage = timeline.stage
    timeline_obj.planned_date = timeline.planned_date
    timeline_obj.notes = sanitize_text(timeline.notes)
    db.commit()
    db.refresh(timeline_obj)
    return timeline_obj

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
