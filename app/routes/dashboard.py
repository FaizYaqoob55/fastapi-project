import csv
from fastapi import APIRouter, Depends, Query, Response,HTTPException
from io import StringIO, BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from app.database import get_db
from app.schemas.dependencies import TechnicalDebtDashboardResponse, get_current_user
from app.models import GrowthSession, Project, Team, TechnicalDebt, User, Deprecation, DeprecationTimeline
from app.model.role import TimeLineStage

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





@router.get("/deprecations")
def deprecation_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    next_30_days = today + timedelta(days=30)

    upcoming_deprecations = db.query(DeprecationTimeline).filter(
        DeprecationTimeline.stage == TimeLineStage.removed,
        DeprecationTimeline.planned_date >= today,
        DeprecationTimeline.planned_date <= next_30_days
    ).count()

    overdue_items = db.query(DeprecationTimeline).filter(
        DeprecationTimeline.stage == TimeLineStage.removed,
        DeprecationTimeline.planned_date < today
    ).count()

    low_count = db.query(Deprecation).filter(Deprecation.impact_level == "low").count()
    medium_count = db.query(Deprecation).filter(Deprecation.impact_level == "medium").count()
    high_count = db.query(Deprecation).filter(Deprecation.impact_level == "high").count()

    return {
        "upcoming_removals": upcoming_deprecations,
        "overdue_items": overdue_items,
        "impact_breakdown": {
            "low": low_count,
            "medium": medium_count,
            "high": high_count
        }
    }
    
@router.get("/deprecation/{deprecation_id}/full-view")
def deprecation_full_view(deprecation_id:int,db:Session=Depends(get_db) ,current_user:User=Depends(get_current_user)):
    deprecation=db.query(Deprecation).filter(Deprecation.id==deprecation_id).first()
    if not deprecation:
        raise HTTPException(status_code=404, detail="Deprecation not found")
    return {"deprecation full view":{
        "deprecation_id":deprecation.id,
        "deprecation item_name":deprecation.item_name,
        "deprecation current_version":deprecation.current_version,
        "deprecation impact level":deprecation.impact_level,
        "deprecation status":deprecation.status,
        "deprecation removed_planned_for":deprecation.removal_planned_for,
    },
    "deprecation timeline":[
        {
            "stage":timeline.stage,
            "planned_date":timeline.planned_date,
            "notes":timeline.notes,
            "created_at":timeline.created_at,
        }
        for timeline in deprecation.timeline
    ],
    "technical debt":[
        {
            "id":debt.id,
            "title":debt.title,
            "status":debt.status,
            "project_id":debt.project_id,
            "due_date":debt.due_date,
        }
        for debt in deprecation.technical_debts
    ]}


@router.get("/export")
def export_deprecations(format: str = "csv", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    deprecations = db.query(Deprecation).all()
    headers = ['ID', 'Project', 'Item', 'Version', 'Depr. In', 'Impact', 'Replacement', 'Type', 'Status', 'Remov. Plan', 'System', 'Users']
    
    data = []
    for dep in deprecations:
        data.append([
            dep.id,
            dep.project_id,
            dep.item_name,
            dep.current_version,
            dep.deprecated_in,
            dep.impact_level,
            dep.replacement,
            dep.type.value if hasattr(dep.type, 'value') else dep.type,
            dep.status,
            dep.removal_planned_for,
            dep.affected_system,
            dep.affected_users_count
        ])

    if format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['id','project_id','item_name','current_version','deprecated_in','impact_level','replacement','type','status','removal_planned_for','affected_system','affected_users_count'])
        writer.writerows(data)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=deprecations.csv"}
        )
    
    elif format == "pdf":
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        elements.append(Paragraph("Deprecations Export", styles['Title']))
        
        table_data = [headers] + data
        # Scale down the font size for PDF to fit more content
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        doc.build(elements)
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=deprecations.pdf"}
        )
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Supported: csv, pdf")

        

