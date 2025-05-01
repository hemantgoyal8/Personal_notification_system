from fastapi import APIRouter, HTTPException, status, Query, Path
from typing import List

from notification_service.app.schemas.notification import NotificationPublic, NotificationUpdateRead
from notification_service.app.db import crud # Using sync crud
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Note: We need a way to get the authenticated user ID.
# In a real scenario, the API Gateway would verify the JWT
# and pass the user ID (e.g., email) in a header or the request context.
# For now, we'll pass userId directly in the path.

@router.get(
    "/user/{user_id}",
    response_model=List[NotificationPublic],
    summary="Get notifications for a user"
)
async def get_notifications_for_user(
    user_id: str = Path(..., description="ID of the user (e.g., email)"),
    unread_only: bool = Query(False, description="Set to true to fetch only unread notifications"),
    skip: int = Query(0, ge=0, description="Number of notifications to skip"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of notifications to return")
):
    """
    Retrieves a list of notifications for the specified user, sorted by most recent first.
    Use the `unread_only` query parameter to filter for unread notifications.
    """
    logger.info(f"Fetching notifications for user {user_id}. Unread only: {unread_only}")
    if unread_only:
        notifications_db = crud.get_unread_notifications_by_user_sync(user_id=user_id, skip=skip, limit=limit)
    else:
        notifications_db = crud.get_notifications_by_user_sync(user_id=user_id, skip=skip, limit=limit)
    
    # Convert NotificationInDB to NotificationPublic for response
    return [NotificationPublic.from_orm(n) for n in notifications_db]


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationPublic,
    summary="Mark a notification as read"
)
async def mark_as_read(
    notification_id: str = Path(..., description="ID of the notification to mark as read"),
    user_id: str = Query(..., description="ID of the user who owns the notification (for verification)") # Pass user_id as query param for now
):
    """
    Marks a specific notification identified by `notification_id` as read.
    Requires `user_id` to ensure the notification belongs to the user making the request.
    (In real app, user_id would come from auth token).
    """
    logger.info(f"Marking notification {notification_id} as read for user {user_id}")
    
    # Validate ObjectId format before hitting DB
    from bson import ObjectId
    if not ObjectId.is_valid(notification_id):
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid notification ID format.")

    updated_notification_db = crud.mark_notification_as_read_sync(
        notification_id=notification_id,
        user_id=user_id
    )

    if updated_notification_db is None:
        # Could be not found, or user mismatch
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or user does not match"
        )
    
    return NotificationPublic.from_orm(updated_notification_db)


@router.patch(
    "/user/{user_id}/read-all",
    status_code=status.HTTP_200_OK,
    summary="Mark all notifications for a user as read"
)
async def mark_all_as_read(
    user_id: str = Path(..., description="ID of the user whose notifications should be marked read")
):
    """
    Marks all unread notifications for the specified user as read.
    Returns the number of notifications that were updated.
    """
    logger.info(f"Marking all notifications as read for user {user_id}")
    modified_count = crud.mark_all_notifications_as_read_sync(user_id=user_id)
    
    return {"message": f"Successfully marked {modified_count} notifications as read.", "updated_count": modified_count}