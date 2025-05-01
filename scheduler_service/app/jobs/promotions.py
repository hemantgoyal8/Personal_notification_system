import logging
import asyncio
import random

# Using mock users for simplicity now
from scheduler_service.app.models.mock_data import mock_users_store, get_random_promotion
# from scheduler_service.app.clients.user_service import get_user_preferences # Use this if switching to real user service calls
from scheduler_service.app.events.producer import publish_message

logger = logging.getLogger(__name__)

async def send_promotional_notifications_job():
    """
    Scheduled job to send promotional notifications to eligible users.
    """
    logger.info("Running promotional notifications job...")
    published_count = 0
    targeted_users = 0

    # Iterate through mock users (replace with User Service call if needed)
    all_user_ids = list(mock_users_store.keys())
    
    # Optional: Select a subset of users for the promotion run
    # sample_size = min(len(all_user_ids), 5) # Example: target up to 5 users per run
    # target_user_ids = random.sample(all_user_ids, sample_size)
    target_user_ids = all_user_ids # Target all mock users for now

    promotion_content = get_random_promotion()

    for user_id in target_user_ids:
        user_data = mock_users_store.get(user_id)
        
        if not user_data:
            logger.warning(f"Mock user {user_id} not found.")
            continue

        # Fetch preferences (currently from mock data)
        preferences = user_data.preferences
        # If using User Service client:
        # preferences = await get_user_preferences(user_id)
        # if preferences is None:
        #     logger.warning(f"Could not fetch preferences for user {user_id}. Skipping promotion.")
        #     continue

        # Check if user wants promotional notifications
        if preferences.get("promotions", False): # Default to False if key missing
            targeted_users += 1
            logger.info(f"User {user_id} is eligible for promotion. Sending...")

            # Construct notification message
            notification_payload = {
                "userId": user_id,
                "type": "promotion",
                "content": promotion_content # Use the selected promotion
            }

            # Publish message to RabbitMQ
            success = await publish_message(notification_payload)
            if success:
                published_count += 1
            else:
                 logger.error(f"Failed to publish promotion to {user_id}")

            # Optional delay
            # await asyncio.sleep(0.1)
        else:
            logger.info(f"User {user_id} opted out of promotions. Skipping.")

    logger.info(f"Promotional notifications job finished. Users targeted: {targeted_users}, Notifications published: {published_count}")