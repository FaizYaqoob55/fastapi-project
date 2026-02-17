from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.dependencies import get_current_user
from app.models import Team, Project, User






router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)

class ProjectBase(BaseModel):
    name: str
    description: str
    status: str
    team_id: int

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id:int
    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify team exists and user is authorized
    team = db.query(Team).filter(Team.id == project.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to create project for this team")
    
    if db.query(Project).filter(Project.name == project.name).first():
        raise HTTPException(status_code=400, detail="Project name already exists")
    
    new_project = Project(
        name=project.name,
        description=project.description,
        status=project.status,
        team_id=project.team_id
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.get("/", response_model=list[ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return projects

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project_update: ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    team = db.query(Team).filter(Team.id == project.team_id).first()
    if team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this project")

    
    if project_update.name:
        project.name = project_update.name
    if project_update.description:
        project.description = project_update.description
    if project_update.status:
        project.status = project_update.status  
    
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project_query = db.query(Project).filter(Project.id == project_id)
    project = project_query.first()
    if project == None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    team = db.query(Team).filter(Team.id == project.team_id).first()
    if team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this project")
    
    project_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT) 
