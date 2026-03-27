from sqlalchemy.orm import Session
from src.models.notification import Notification
from src.schemas.notification import NotificationCreate
from src.core.exceptions import BusinessException
from typing import List

def create_notification(db: Session, obj_in: NotificationCreate) -> Notification:
    db_obj = Notification(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_user_notifications(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Notification]:
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

def get_unread_count(db: Session, user_id: int) -> int:
    return db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).count()

def mark_as_read(db: Session, user_id: int, notification_id: int) -> Notification:
    notification = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()
    if not notification:
        raise BusinessException(code=404, detail="Notification not found.")
    
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification

def mark_all_as_read(db: Session, user_id: int) -> str:
    db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).update({"is_read": True})
    db.commit()
    return "All notifications marked as read."
