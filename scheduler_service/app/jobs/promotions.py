# scheduler_service/app/jobs/promotions.py
import logging
import asyncio
import random

from ..models.mock_data import MockUser, mock_users_store, get_random_promotion # Import MockUser for type hinting
from ..events import producer 
from ..core.config import settings, logger

async def send_promotional_notifications_job():
    """
    Scheduled job to send promotional notifications to eligible users.
    """
    logger.info("Running promotional notifications job...")
    published_count = 0
    targeted_users = 0

    all_user_keys = list(mock_users_store.keys()) # These keys are user_ids like "user1@example.com"
    target_user_keys = all_user_keys 

    promotion_details = get_random_promotion() 
    if not promotion_details:
        logger.warning("No promotions available to send.")
        return

    for user_key in target_user_keys: # user_key is e.g., "user1@example.com"
        user_data: Optional[MockUser] = mock_users_store.get(user_key) # Get the MockUser object
        
        if not user_data:
            logger.warning(f"Mock user with key '{user_key}' not found for promotion.")
            continue

        # Access the 'preferences' attribute (which is a dict) from the MockUser object
        preferences_dict = user_data.preferences 

        # Check if user wants promotional notifications using .get() on the preferences_dict
        if preferences_dict.get("promotions", False): 
            targeted_users += 1
            # Use the userId attribute from the MockUser object for logging and payload
            user_identifier_for_notification = user_data.userId 
            logger.info(f"User '{user_identifier_for_notification}' is eligible for promotion. Preparing to send...")

            message_body = {
                "user_id": user_identifier_for_notification, 
                "type": "promotion",
                "title": promotion_details.get("title", "Special Offer!"),
                "body": promotion_details.get("description", "Check out our latest promotions."),
                "data": { 
                    "promotion_id": promotion_details.get("id"),
                    "discount_code": promotion_details.get("code") 
                }
            }
            
            exchange_name = settings.PROMOTION_EVENTS_EXCHANGE
            routing_key = f"promotions.user.{user_identifier_for_notification}" # More specific routing key

            await producer.publish_message(
                exchange_name=exchange_name,
                routing_key=routing_key,
                message_body=message_body
            )
            published_count += 1 
            logger.info(f"Promotion message queued for user '{user_identifier_for_notification}'.")
        else:
            user_identifier_for_logging = user_data.userId
            logger.info(f"User '{user_identifier_for_logging}' opted out of promotions or preference not set/found. Skipping.")

    logger.info(f"Promotional notifications job finished. Eligible users targeted: {targeted_users}, Notifications queued: {published_count}")