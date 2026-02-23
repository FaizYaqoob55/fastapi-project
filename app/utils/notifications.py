from sqlalchemy.orm import Session
from app.model.role import NotificationType
from app.models import Notification
from fastapi import APIRouter,Depends
from app.database import get_db
from app.schemas.dependencies import NotificationResponse
from app.schemas.dependencies import get_current_user
from app.models import User
from datetime import datetime

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

    