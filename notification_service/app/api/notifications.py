from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime # For dummy data example

# Corrected relative imports for schemas and CRUD
from ..schemas.notification import NotificationPublic, NotificationUpdateRead 
from ..db import crud 
from ..core.config import logger # Import logger if needed

router = APIRouter() 

@router.get("/{user_id}", response_model=List[NotificationPublic])
def get_notifications_for_user_api(user_id: str, read: Optional[bool] = None):
    logger.info(f"API: Fetching notifications for user_id: {user_id}, read_status: {read}")
    notifications = crud.get_notifications_for_user(user_id=user_id, read_status=read)
    return notifications

@router.patch("/{notification_id}/read", response_model=NotificationPublic)
def mark_notification_as_read_api(notification_id: str, read_status: NotificationUpdateRead):
    logger.info(f"API: Marking notification {notification_id} as read={read_status.read}")
    updated_notification = crud.update_notification_read_status(notification_id=notification_id, read=read_status.read)
    if not updated_notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found or update failed")
    return updated_notification