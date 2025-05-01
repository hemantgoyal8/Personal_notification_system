from pymongo.collection import Collection
from bson import ObjectId
from typing import List, Optional
from datetime import datetime

from notification_service.app.db.database import get_notification_collection, notification_helper
from notification_service.app.schemas.notification import NotificationCreate, NotificationInDB
import logging

logger = logging.getLogger(__name__)

def create_notification_sync(notification_in: NotificationCreate) -> Optional[NotificationInDB]:
    """Stores a new notification in the database (Synchronous)."""
    collection = get_notification_collection()
    notification_data = notification_in.dict()
    # Ensure sentAt is set (though default_factory in Pydantic should handle it)
    notification_data.setdefault("sentAt", datetime.utcnow())

    try:
        result = collection.insert_one(notification_data)
        if result.inserted_id:
            created_doc = collection.find_one({"_id": result.inserted_id})
            if created_doc:
                 # Convert to NotificationInDB for consistent return type
                 # Handle the _id field mapping
                 created_doc['id'] = created_doc.pop('_id')
                 return NotificationInDB(**created_doc)
            else:
                logger.error(f"Failed to retrieve notification immediately after insertion with id {result.inserted_id}")
                return None
        else:
            logger.error("Failed to insert notification, insert_one returned no ID.")
            return None
    except Exception as e:
        logger.error(f"Error creating notification for user {notification_in.userId}: {e}")
        return None

def get_notifications_by_user_sync(user_id: str, skip: int = 0, limit: int = 100) -> List[NotificationInDB]:
    """Retrieves notifications for a specific user (Synchronous)."""
    collection = get_notification_collection()
    try:
        notifications_cursor = collection.find({"userId": user_id})\
                                         .sort("sentAt", -1)\
                                         .skip(skip)\
                                         .limit(limit)
        
        notifications = []
        for doc in notifications_cursor:
            doc['id'] = doc.pop('_id') # Map _id to id
            notifications.append(NotificationInDB(**doc))
        return notifications
    except Exception as e:
        logger.error(f"Error retrieving notifications for user {user_id}: {e}")
        return []

def get_unread_notifications_by_user_sync(user_id: str, skip: int = 0, limit: int = 100) -> List[NotificationInDB]:
    """Retrieves only unread notifications for a specific user (Synchronous)."""
    collection = get_notification_collection()
    try:
        notifications_cursor = collection.find({"userId": user_id, "read": False})\
                                         .sort("sentAt", -1)\
                                         .skip(skip)\
                                         .limit(limit)

        notifications = []
        for doc in notifications_cursor:
            doc['id'] = doc.pop('_id') # Map _id to id
            notifications.append(NotificationInDB(**doc))
        return notifications
    except Exception as e:
        logger.error(f"Error retrieving unread notifications for user {user_id}: {e}")
        return []


def mark_notification_as_read_sync(notification_id: str, user_id: str) -> Optional[NotificationInDB]:
    """Marks a specific notification as read (Synchronous)."""
    collection = get_notification_collection()
    try:
        if not ObjectId.is_valid(notification_id):
             logger.warning(f"Invalid ObjectId format for notification_id: {notification_id}")
             return None

        obj_id = ObjectId(notification_id)

        result = collection.update_one(
            {"_id": obj_id, "userId": user_id}, # Ensure user owns the notification
            {"$set": {"read": True}}
        )

        if result.matched_count == 0:
            logger.warning(f"Notification not found or user mismatch for id {notification_id} and user {user_id}")
            return None
        elif result.modified_count == 0:
             logger.info(f"Notification {notification_id} was already marked as read.")
             # Fetch and return the existing doc
             updated_doc = collection.find_one({"_id": obj_id})
             if updated_doc:
                 updated_doc['id'] = updated_doc.pop('_id')
                 return NotificationInDB(**updated_doc)
             else: # Should not happen if matched_count > 0
                 return None
        else: # Modified count == 1
             updated_doc = collection.find_one({"_id": obj_id})
             if updated_doc:
                 updated_doc['id'] = updated_doc.pop('_id')
                 return NotificationInDB(**updated_doc)
             else: # Should not happen
                 logger.error(f"Failed to retrieve notification {notification_id} after update.")
                 return None

    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read for user {user_id}: {e}")
        return None

def mark_all_notifications_as_read_sync(user_id: str) -> int:
    """Marks all notifications for a user as read (Synchronous). Returns count modified."""
    collection = get_notification_collection()
    try:
        result = collection.update_many(
            {"userId": user_id, "read": False},
            {"$set": {"read": True}}
        )
        logger.info(f"Marked {result.modified_count} notifications as read for user {user_id}.")
        return result.modified_count
    except Exception as e:
        logger.error(f"Error marking all notifications as read for user {user_id}: {e}")
        return 0 # Indicate failure or no notifications modified