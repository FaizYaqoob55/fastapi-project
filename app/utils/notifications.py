from sqlalchemy.orm import Session
from app.model.role import NotificationType
from app.models import Notification
from fastapi import APIRouter, BackgroundTasks,Depends
from app.database import get_db
from app.schemas.dependencies import NotificationResponse
from app.schemas.dependencies import get_current_user
from app.models import User
from datetime import datetime
from app.utils.email_service import send_email_simulation 

from app.utils.email_templates import action_item_due_template, mention_template, session_remainder_template

router =APIRouter(prefix="/notification",
        tags=["Notification"]
)


def create_notification(
        db:Session,
        user_id:int,
        type:NotificationType,
        message:str
):
    notification=Notification(user_id=user_id,
                             type=type,
                             message=message
                             )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@router.get('/',response_model=list[NotificationResponse])
def get_my_notification(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
                        return db.query(Notification).filter(
                                Notification.user_id==current_user.id).order_by(
                                        Notification.created_at.desc()).all()


@router.patch('/{notification_id}/read')
def mark_as_read(
                notification_id: int,
                db:Session=Depends(get_db),
                current_user:User=Depends(get_current_user)
):
        notification=db.query(Notification).filter(Notification.id==notification_id).first()
        if notification:
                notification.is_read=True
                db.commit()
                return {'message':'Notification marked as read'}

    



def dispatch_notification_email(background_task:BackgroundTasks,user:User,notification_type:NotificationType,payload:dict):
        if user.email_notification_enabled:
                return
        if notification_type==NotificationType.session_reminder:
                subject="Growth Session Reminder"
                body=session_remainder_template(
                       user.name,payload['session_title'],payload['session_date']
                )
        elif notification_type==NotificationType.action_item_due:
                subject="Action Item Due Reminder"
                body=action_item_due_template(
                        user.name,payload['action_title']
                )
        elif notification_type==NotificationType.mention:
                subject="You were mentioned in a session note"
                body=mention_template(user.name)
        else:
                return
        background_task.add_task(
                send_email_simulation,
                user.name,
                subject,
                body
        )