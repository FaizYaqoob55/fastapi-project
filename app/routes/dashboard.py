from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from app.database import get_db
from app.schemas.dependencies import get_current_user
from app.models import GrowthSession, Team, User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/growth-session")
def growth_session_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_sessions = db.query(func.count(GrowthSession.id)).scalar()
    completed_sessions = db.query(func.count(GrowthSession.id)).filter(GrowthSession.status == "completed").scalar()
    upcoming_sessions = db.query(func.count(GrowthSession.id)).filter(GrowthSession.date >= date.today()).scalar()
    team_breakdown = db.query(
        Team.name,
        func.count(GrowthSession.id)
    ).join(GrowthSession, GrowthSession.team_id == Team.id).group_by(Team.name).all()
    teams = [
        {
            "team_name": team_name,
            "session_count": session_count
        }
        for team_name, session_count in team_breakdown
    ]
    monthly = (
        db.query(
            func.date_trunc('month', GrowthSession.date).label('month'),
            func.count(GrowthSession.id)
        )
        .group_by('month')
        .order_by('month')
        .all()
    )
    monthly_data = [
        {"month": m.strftime("%Y-%m"), "session": c}
        for m, c in monthly
    ]

    if total_sessions == 0:
        completed_sessions = 0
    else:
        completed_sessions = round((completed_sessions / total_sessions) * 100, 2)
    other_count = total_sessions - sum(t["session_count"] for t in teams)
    team_wise = teams.copy()
    if other_count > 0:
        team_wise.append({"team_name": "Other", "session_count": other_count})

    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "upcoming_sessions": upcoming_sessions,
        "completed_rate": completed_sessions,
        "monthly_data": monthly_data,
        "team_wise": team_wise,
        "monthly_trend": monthly_data,
    }
