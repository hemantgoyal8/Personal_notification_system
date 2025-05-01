import logging
import asyncio

from scheduler_service.app.models.mock_data import mock_orders_store, update_mock_order_status
from scheduler_service.app.events.producer import publish_message

logger = logging.getLogger(__name__)

async def check_order_statuses_job():
    """
    Scheduled job to check mock order statuses and publish updates.
    """
    logger.info("Running order status check job...")
    updated_count = 0
    published_count = 0

    # Create a copy of keys to avoid issues if dict changes during iteration (though unlikely here)
    order_ids = list(mock_orders_store.keys())

    for order_id in order_ids:
        updated_order = update_mock_order_status(order_id) # This function contains the update logic and timing checks

        if updated_order:
            updated_count += 1
            logger.info(f"Order {updated_order.orderId} status changed to '{updated_order.status}'. Publishing update.")
            
            # Construct notification message
            notification_payload = {
                "userId": updated_order.userId,
                "type": "order_update",
                "content": {
                    "title": f"Order {updated_order.orderId} Update",
                    "body": f"Your order status is now: {updated_order.status}",
                    "link": f"/orders/{updated_order.orderId}" # Example link
                }
            }
            
            # Publish message to RabbitMQ
            success = await publish_message(notification_payload)
            if success:
                published_count += 1
            else:
                 logger.error(f"Failed to publish order update for {order_id}")

            # Optional: Add a small delay between messages if needed
            # await asyncio.sleep(0.1)

    logger.info(f"Order status check job finished. Orders updated: {updated_count}, Notifications published: {published_count}")