import csv
from fastapi import APIRouter, Depends, Query, Response
from io import StringIO
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from app.database import get_db
from app.schemas.dependencies import TechnicalDebtDashboardResponse, get_current_user
from app.models import GrowthSession, Project, Team, TechnicalDebt, User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])









def technical_debt_dashboard(db:Session,again_days:int =30):
    total_debts = db.query(func.count(TechnicalDebt.id)).scalar()
    priority_breakdown = dict(db.query(TechnicalDebt.priority, func.count(TechnicalDebt.id)).group_by(TechnicalDebt.priority).all())
    by_status = dict(db.query(TechnicalDebt.status, func.count(TechnicalDebt.id)).group_by(TechnicalDebt.status).all())
    project_breakdown = db.query(Project.name, func.count(TechnicalDebt.id)).join(TechnicalDebt, TechnicalDebt.project_id == Project.id).group_by(Project.name).all()
    monthly_trend = db.query(func.date_trunc('month', TechnicalDebt.created_at).label('month'), func.count(TechnicalDebt.id)).group_by('month').order_by('month').all()
    again_count = db.query(func.count(TechnicalDebt.id)).filter(TechnicalDebt.created_at >= date.today() - timedelta(days=again_days)).scalar()
    return {
        "total_debts": total_debts,
        "priority_breakdown": priority_breakdown,
        "by_status": by_status,
        "project_breakdown": [{"project_name": p, "debt_count": c} for p, c in project_breakdown],
        "monthly_trend": [{"month": m.strftime("%Y-%m"), "debt_count": c} for m, c in monthly_trend],
        "again_count": again_count
    }









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

@router.get("/technical-debt",response_model=TechnicalDebtDashboardResponse)
def technical_debt_dashboard_endpoint(db: Session = Depends(get_db), again_days: int = Query(30, ge=0), current_user: User = Depends(get_current_user)):
    return technical_debt_dashboard(db, again_days)



@router.get("/technical_debt/export")
def export_technical_debt_csv(priority: str |None=None ,status: str |None=None, project_id: int |None=None,db: Session = Depends(get_db)):
    query = db.query(TechnicalDebt)
    if priority:
        query = query.filter(TechnicalDebt.priority == priority)
    if status:
        query = query.filter(TechnicalDebt.status == status)
    if project_id is not None:
        query = query.filter(TechnicalDebt.project_id == project_id)
    debts = query.all()
    output=StringIO()
    writer=csv.writer(output)
    writer.writerow(['id','title','description','priority','status','project_id','due_date','created_at'])
    for debt in debts:
        writer.writerow([debt.id, debt.title, debt.description, debt.priority, debt.status, debt.project_id, debt.due_date, debt.created_at])
    return Response(content=output.getvalue(),
                     media_type="text/csv",
                       headers={"Content-Disposition": "attachment; filename=technical_debts.csv"})

