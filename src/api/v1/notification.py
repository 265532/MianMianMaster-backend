from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Any
from src.api.deps import get_db, get_current_active_user
from src.schemas.notification import Notification, NotificationCreate
from src.schemas.system import ResponseModel
from src.services import notification_service
from src.models.user import User as UserModel

router = APIRouter()

@router.get("", response_model=ResponseModel[List[Notification]])
def get_notifications(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    notifications = notification_service.get_user_notifications(db, current_user.id, skip, limit)
    return ResponseModel(data=notifications)

@router.get("/unread-count", response_model=ResponseModel[int])
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    count = notification_service.get_unread_count(db, current_user.id)
    return ResponseModel(data=count)

@router.put("/{notification_id}/read", response_model=ResponseModel[Notification])
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    notification = notification_service.mark_as_read(db, current_user.id, notification_id)
    return ResponseModel(data=notification)

@router.put("/read-all", response_model=ResponseModel[str])
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    message = notification_service.mark_all_as_read(db, current_user.id)
    return ResponseModel(data=message)

# For testing / internal system usage
@router.post("", response_model=ResponseModel[Notification])
def create_notification(
    notification_in: NotificationCreate,
    db: Session = Depends(get_db)
) -> Any:
    notification = notification_service.create_notification(db, notification_in)
    return ResponseModel(data=notification)
