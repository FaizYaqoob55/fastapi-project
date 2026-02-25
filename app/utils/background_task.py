from app.utils.email_service import send_email_simulation
from fastapi import BackgroundTasks
from app.utils.email_templates import session_remainder_template


def send_email_task(to_email,subject,body):
        send_email_simulation(to_email,subject,body)




@router.post('/')
def create_session(
        data:GrowthSessionCreate,
        background_tasks:BackgroundTasks,
        
):
        
        email_body=session_remainder_template(
                user_name=current_user.name,
                session_title=session.title,
                session_date=session.date
                )
        background_tasks.add_task(send_email_task,current_user.email,"Growth Session Reminder",email_body)

        return session