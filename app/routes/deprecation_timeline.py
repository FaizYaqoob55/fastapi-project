from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User,Deprecation,DeprecationTimeline
from app.schemas.dependencies import get_current_user,DeprecationTimelineCreate
from app.model.role import TimeLineStage,UserRole
from app.utils.security import sanitize_text
from app.models import Project


router = APIRouter(
    prefix="/deprecation_timeline",
    tags=["Deprecation Timeline"]
)



@router.post("/deprecations/{deprecation_id}/timeline")
def create_deprecation_timeline(
    deprecation_id: int, 
    timeline_data: DeprecationTimelineCreate,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # 1. Fetch Deprecation with Project/Team Info (Optimized)
    deprecation = db.query(Deprecation).join(Project).filter(Deprecation.id == deprecation_id).first()
    
    if not deprecation:
        raise HTTPException(status_code=404, detail="Deprecation notice not found.")

    # 2. RBAC Check (Admin or Team Member)
    user_team_ids = [t.id for t in current_user.teams]
    if current_user.role != UserRole.admin and deprecation.project.team_id not in user_team_ids:
        raise HTTPException(status_code=403, detail="Not authorized to create timeline for this deprecation.")

    # 3. Check if Stage already exists (Ek stage ek hi baar honi chahiye)
    existing = db.query(DeprecationTimeline).filter(
        DeprecationTimeline.deprecation_id == deprecation_id,
        DeprecationTimeline.stage == timeline_data.stage
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"Stage '{timeline_data.stage}' stage already exists.")
    new_timeline = DeprecationTimeline(
        deprecation_id=deprecation_id,
        stage=timeline_data.stage,
        planned_date=timeline_data.planned_date,
        notes=sanitize_text(timeline_data.notes)
    )

    db.add(new_timeline)
    db.commit()
    db.refresh(new_timeline)
    return new_timeline


@router.get("/deprecations/{deprecation_id}/timeline")
def get_deprecation_timeline(
    deprecation_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    deprecation = db.query(Deprecation).filter(Deprecation.id == deprecation_id).first()
    
    if not deprecation:
        raise HTTPException(status_code=404, detail="Deprecation notice not found.")

    user_team_ids = [t.id for t in current_user.teams]
    if current_user.role != UserRole.admin and deprecation.project.team_id not in user_team_ids:
        raise HTTPException(status_code=403, detail="Not authorized to view this timeline.")

    return db.query(DeprecationTimeline).filter(
        DeprecationTimeline.deprecation_id == deprecation_id
    ).order_by(DeprecationTimeline.planned_date.asc()).all()

@router.put("/deprecations/{deprecation_id}/timeline/{timeline_id}")
def update_deprecation_timeline(
    deprecation_id: int, 
    timeline_id: int, 
    timeline_data: DeprecationTimelineCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # 1. Fetch Timeline and verify it belongs to the Deprecation
    timeline_obj = db.query(DeprecationTimeline).filter(
        DeprecationTimeline.id == timeline_id,
        DeprecationTimeline.deprecation_id == deprecation_id
    ).first()

    if not timeline_obj:
        raise HTTPException(status_code=404, detail="Timeline record not found.")

    # 2. RBAC Check using Joins (Fastest way)
    dep = db.query(Deprecation).join(Project).filter(Deprecation.id == deprecation_id).first()
    
    user_team_ids = [t.id for t in current_user.teams]
    if current_user.role != UserRole.admin and dep.project.team_id not in user_team_ids:
        raise HTTPException(status_code=403, detail="Not authorized to update.")

    # 3. Status Lock logic
    if timeline_obj.stage == TimeLineStage.removed:
        raise HTTPException(status_code=400, detail="Removed stage not allowed to be updated.")

    # 4. Update with Sanitization
    timeline_obj.stage = timeline_data.stage
    timeline_obj.planned_date = timeline_data.planned_date
    timeline_obj.notes = sanitize_text(timeline_data.notes)
    
    db.commit()
    db.refresh(timeline_obj)
    return timeline_obj


@router.delete("/deprecations/{deprecation_id}/timeline/{timeline_id}")
def delete_deprecation_timeline(
    deprecation_id: int, 
    timeline_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # 1. Fetch & Verify Ownership
    timeline = db.query(DeprecationTimeline).filter(
        DeprecationTimeline.id == timeline_id,
        DeprecationTimeline.deprecation_id == deprecation_id
    ).first()

    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline record not found.")

    # 2. Security Check
    dep = db.query(Deprecation).join(Project).filter(Deprecation.id == deprecation_id).first()
    user_team_ids = [t.id for t in current_user.teams]
    
    if current_user.role != UserRole.admin and dep.project.team_id not in user_team_ids:
        raise HTTPException(status_code=403, detail="Not authorized to delete.")

    if timeline.stage == TimeLineStage.removed:
        raise HTTPException(status_code=400, detail="Historical records not allowed to be deleted.")

    db.delete(timeline)
    db.commit()
    return {"message": "Timeline deleted successfully"}