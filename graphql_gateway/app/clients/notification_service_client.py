import logging
from typing import Optional, Dict, Any, List
import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = settings.NOTIFICATION_SERVICE_BASE_URL

# Note: Notification service endpoints currently take user_id in path/query.
# In a real system with gateway auth, you might pass the authenticated user_id
# via a trusted header from the gateway, or the service might verify the token itself.
# Here, we pass the user_id explicitly as required by the current Notification Service API.

async def get_notifications(user_id: str, unread_only: bool, skip: int, limit: int) -> Optional[List[Dict[str, Any]]]:
    """Calls the Notification Service to get notifications for a user."""
    url = f"{BASE_URL}/notifications/user/{user_id}"
    params = {"unread_only": unread_only, "skip": skip, "limit": limit}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Notification Service Error (GetNotifications): {e.response.status_code} - {e.response.text}")
            raise Exception("Failed to fetch notifications")
        except httpx.RequestError as e:
            logger.error(f"Notification Service Request Error (GetNotifications): {e}")
            raise Exception("Could not connect to Notification Service")
        except Exception as e:
            logger.error(f"Unexpected Error (GetNotifications): {e}", exc_info=True)
            raise Exception("An unexpected error occurred fetching notifications")


async def mark_notification_read(user_id: str, notification_id: str) -> Optional[Dict[str, Any]]:
    """Calls the Notification Service to mark a notification as read."""
    url = f"{BASE_URL}/notifications/{notification_id}/read"
    # Pass user_id as query param as required by the current Notification Service API
    params = {"user_id": user_id} 
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # PATCH request with no body, just query params
            response = await client.patch(url, params=params) 
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Notification Service Error (MarkRead): {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 404:
                 raise Exception("Notification not found or does not belong to user")
            raise Exception("Failed to mark notification as read")
        except httpx.RequestError as e:
            logger.error(f"Notification Service Request Error (MarkRead): {e}")
            raise Exception("Could not connect to Notification Service")
        except Exception as e:
            logger.error(f"Unexpected Error (MarkRead): {e}", exc_info=True)
            raise Exception("An unexpected error occurred marking notification as read")


async def mark_all_notifications_read(user_id: str) -> Optional[Dict[str, Any]]:
    """Calls the Notification Service to mark all notifications for a user as read."""
    url = f"{BASE_URL}/notifications/user/{user_id}/read-all"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.patch(url) # PATCH request with no body
            response.raise_for_status()
            return response.json() # Returns {"message": "...", "updated_count": ...}
        except httpx.HTTPStatusError as e:
            logger.error(f"Notification Service Error (MarkAllRead): {e.response.status_code} - {e.response.text}")
            raise Exception("Failed to mark all notifications as read")
        except httpx.RequestError as e:
            logger.error(f"Notification Service Request Error (MarkAllRead): {e}")
            raise Exception("Could not connect to Notification Service")
        except Exception as e:
            logger.error(f"Unexpected Error (MarkAllRead): {e}", exc_info=True)
            raise Exception("An unexpected error occurred marking all notifications as read")