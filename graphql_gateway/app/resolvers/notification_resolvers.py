import strawberry
import logging
from typing import List, Optional
from datetime import datetime

from ..schemas_gql.types import NotificationType, NotificationContentType, MarkReadResponseType
from ..clients import notification_service_client
from ..auth.context import GraphQLContext

logger = logging.getLogger(__name__)

# Helper function to map dict to NotificationType
def _map_to_notification_type(notif_data: dict) -> NotificationType:
    content_data = notif_data.get("content", {})
    content = NotificationContentType(
        title=content_data.get("title", "N/A"),
        body=content_data.get("body", ""),
        link=content_data.get("link")
    )
    # Ensure sentAt is parsed correctly if it's a string
    sent_at_raw = notif_data.get("sentAt")
    sent_at = datetime.fromisoformat(sent_at_raw) if isinstance(sent_at_raw, str) else sent_at_raw

    return NotificationType(
        id=notif_data.get("id"),
        userId=notif_data.get("userId"),
        type=notif_data.get("type"),
        content=content,
        sentAt=sent_at,
        read=notif_data.get("read", False)
    )


async def resolve_get_notifications(
    info: GraphQLContext,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 100
) -> List[NotificationType]:
    """Resolver to get notifications for the authenticated user."""
    context = info.context
    if not context.user_id:
        logger.warning("Attempted to access 'notifications' without authentication.")
        raise Exception("Authentication required")

    logger.info(f"Fetching notifications for user: {context.user_id} (unread_only={unread_only}, skip={skip}, limit={limit})")
    
    notifications_data = await notification_service_client.get_notifications(
        user_id=context.user_id,
        unread_only=unread_only,
        skip=skip,
        limit=limit
    )
    
    if notifications_data is None:
        return [] # Return empty list if client returns None

    return [_map_to_notification_type(n) for n in notifications_data]


async def resolve_mark_notification_read(info: "GraphQLContext", notification_id: str) -> NotificationType:
    """Resolver to mark a single notification as read."""
    context = info.context
    if not context.user_id:
        logger.warning("Attempted to 'markNotificationRead' without authentication.")
        raise Exception("Authentication required")

    logger.info(f"Attempting to mark notification {notification_id} read for user {context.user_id}")
    
    # Client raises exceptions on failure
    updated_notification_data = await notification_service_client.mark_notification_read(
        user_id=context.user_id,
        notification_id=notification_id
    )
    
    return _map_to_notification_type(updated_notification_data)


async def resolve_mark_all_notifications_read(info: "strawberry.types.Info[GraphQLContext]") -> MarkReadResponseType:
    """Resolver to mark all notifications as read."""
    context = info.context
    if not context.user_id:
        logger.warning("Attempted to 'markAllNotificationsRead' without authentication.")
        raise Exception("Authentication required")

    logger.info(f"Attempting to mark all notifications read for user {context.user_id}")
    
    # Client raises exceptions on failure
    response_data = await notification_service_client.mark_all_notifications_read(
        user_id=context.user_id
    )

    return MarkReadResponseType(
        message=response_data.get("message", "Operation status unknown"),
        updated_count=response_data.get("updated_count", 0)
    )