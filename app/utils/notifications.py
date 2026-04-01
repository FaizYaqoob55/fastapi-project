from sqlalchemy.orm import Session
from app.model.role import NotificationType
from app.models import Notification
from fastapi import APIRouter, BackgroundTasks,Depends, HTTPException
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


def dispatch_notification_email(background_task: BackgroundTasks, user: User, notification_type: NotificationType, payload: dict):
    # 1. SAHI LOGIC: Agar enabled NAHI hai, to return karo
    if not user.email_notification_enabled:
        return

    subject = ""
    body = ""

    # 2. Template Mapping
    if notification_type == NotificationType.session_reminder:
        subject = "📅 Growth Session Reminder"
        body = session_remainder_template(
            user.name, payload.get('session_title'), payload.get('session_date')
        )
    elif notification_type == NotificationType.action_item_due:
        subject = "⏳ Action Item Due Reminder"
        body = action_item_due_template(
            user.name, payload.get('action_title')
        )
    elif notification_type == NotificationType.mention:
        subject = "🏷️ You were mentioned in a session note"
        body = mention_template(user.name)
    else:
        return

    # 3. Add to background task
    background_task.add_task(
        send_email_simulation,
        user.email, 
        subject,
        body
    )

@router.patch('/{notification_id}/read')
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id, 
        Notification.user_id == current_user.id 
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()
    return {'message': 'Notification marked as read'}