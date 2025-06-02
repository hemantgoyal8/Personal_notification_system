# scheduler_service/app/jobs/recommendations.py
import logging
import asyncio
import random

from ..events.producer import RabbitMQProducer # Import the class
from ..core.config import settings, logger # Assuming logger is from your config

# If logger is not from config:
# logger = logging.getLogger(__name__)

fake_titles = [
    "Recommended: New Laptops",
    "Based on your shopping: Headphones",
    "Flash Sale: Gaming Chairs",
    "Exclusive: Smartwatches Under ₹999"
]

fake_bodies = [
    "Get your favorite tech products now!",
    "Trending picks just for you.",
    "Don't miss out on this limited-time deal.",
    "Your style, your price — shop now."
]

async def generate_recommendation_notifications_job(): # Renamed to follow pattern
    """
    Scheduled job to generate and send recommendation notifications.
    """
    logger.info("Running recommendation notifications job...")
    producer = RabbitMQProducer() # Uses default RABBITMQ_URL from settings
    
    try:
        await producer.connect() # Establish connection and channel

        published_count = 0
        for user_id_num in range(1, 4):  # Simulate for 3 users (user_id 1, 2, 3)
            user_id_str = str(user_id_num) # Assuming userId is expected as string
            title = random.choice(fake_titles)
            body = random.choice(fake_bodies)

            # Construct message body
            message_body = {
                "user_id": user_id_str, # Ensure field name matches notification_service
                "type": "recommendation",
                "title": title, # More descriptive title
                "body": body,
                "data": { # Optional structured data
                    "link": "https://example.com/recommendations"
                }
            }

            # Define exchange and routing key for recommendation messages
            exchange_name = settings.RECOMMENDATION_EVENTS_EXCHANGE # Get from settings
            # Routing key for recommendations, can be general or user-specific
            routing_key = f"recommendation.user.{user_id_str}" # Example user-specific routing

            success = await producer.send_message(
                exchange_name=exchange_name,
                routing_key=routing_key,
                message_body=message_body
            )
            
            if success:
                logger.info(f"Recommendation message queued for user {user_id_str}.")
                published_count += 1
            else:
                logger.error(f"Failed to queue recommendation for user {user_id_str}.")
            
            # await asyncio.sleep(0.1) # Optional delay

        logger.info(f"Recommendation notifications job finished. Notifications queued: {published_count}")

    except ConnectionError as ce: # Catch connection error from producer.connect() or send_message()
        logger.error(f"Recommendation job failed: Could not connect to RabbitMQ. {ce}")
    except Exception as e:
        logger.error(f"Unexpected error in recommendation job: {e}", exc_info=True)
    finally:
        await producer.close() # Ensure connection is closed