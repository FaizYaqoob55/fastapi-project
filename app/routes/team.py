from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Team, TeamMember, User
from app.schemas.dependencies import TeamCreate, TeamResponse, TeamUpdate, TeamMemberCreate
from app.schemas.dependencies import get_current_user, requires_role
from app.models import User

router = APIRouter(
    prefix="/teams",
    tags=["Teams"]
)


@router.post("/", response_model=TeamResponse,status_code=status.HTTP_201_CREATED)
def create_team(team: TeamCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_team = Team(name=team.name, lead_id=current_user.id)
    existing_team = db.query(Team).filter(Team.name == team.name).first()
    if existing_team:
        raise HTTPException(status_code=400, detail="Team name already exists")
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    return new_team

@router.get("/", response_model=list[TeamResponse])
def get_teams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    teams = db.query(Team).all()
    return teams

@router.put("/{team_id}", response_model=TeamResponse)
def update_team(team_id: int, team_update: TeamUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this team")
    if team_update.name:
        existing_team = db.query(Team).filter(Team.name == team_update.name).first()
        if existing_team and existing_team.id != team_id:
            raise HTTPException(status_code=400, detail="Team name already exists")

    if team_update.name:
        team.name = team_update.name
    db.commit()
    db.refresh(team)
    return team




@router.post("/{team_id}/members")
def add_member(team_id: int, member: TeamMemberCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add members to this team")
    user = db.query(User).filter(User.id == member.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user in team.members:
        raise HTTPException(status_code=400, detail="User is already a member of the team")
    team.members.append(user)
    db.commit()
    return {"message": "Member added successfully"}

@router.delete("/{team_id}/remove-member")
def remove_member(team_id: int, member: TeamMemberCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to remove members from this team")
    user = db.query(User).filter(User.id == member.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user not in team.members:
        raise HTTPException(status_code=400, detail="User is not a member of the team")
    team.members.remove(user)
    db.commit()
    return {"message": "Member removed successfully"}



@router.delete("/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this team")
    db.delete(team)
    db.commit()
    return {"message": "Team deleted successfully"}