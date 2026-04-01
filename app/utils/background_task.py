from fastapi import APIRouter, BackgroundTasks, Depends
from app.models import User
from app.utils.email_service import send_email_simulation
from app.utils.email_templates import session_remainder_template
from app.routes.growth_session import GrowthSessionCreate
from app.schemas.dependencies import get_current_user

router = APIRouter() 

def send_email_task(to_email: str, subject: str, body: str):
    # Ye function background mein chale ga
    send_email_simulation(to_email, subject, body)

@router.post('/')
def create_session(
    data: GrowthSessionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    # 1. Template mein 'data' use karein (jo user ne bheja hai)
    email_body = session_remainder_template(
        user_name=current_user.name,
        session_title=data.title, # 'session' ki jagah 'data'
        session_date=data.date     # 'session' ki jagah 'data'
    )

    # 2. Background task add karein
    background_tasks.add_task(
        send_email_task, 
        current_user.email, 
        "Growth Session Reminder", 
        email_body
    )

    # 3. Success Response bhejein
    return {"message": "Session created and email is being sent in background", "data": data}