# scheduler_service/app/jobs/order_updates.py
import logging
import asyncio

# Corrected relative imports
from ..core.config import settings, logger # Assuming logger is from your config
from ..models.mock_data import mock_orders_store, update_mock_order_status
from ..events import producer # Import the producer module

async def check_order_statuses_job():
    logger.info("Running order status check job...")
    updated_count = 0
    published_attempts = 0 # Renamed from published_count for clarity

    order_ids = list(mock_orders_store.keys())

    for order_id_key in order_ids:
        # update_mock_order_status now returns the updated order object or None if no update
        # It also internally updates the mock_orders_store
        updated_order_data = update_mock_order_status(order_id_key) 

        if updated_order_data: # If an update occurred and data is returned
            updated_count += 1
            # Assuming updated_order_data is a dictionary matching your mock order structure
            order_id_from_data = updated_order_data.get("orderId") # Or however orderId is stored
            new_status = updated_order_data.get("status")
            user_id_for_order = updated_order_data.get("userId")

            logger.info(f"Order {order_id_from_data} status changed to '{new_status}'. Publishing update for user {user_id_for_order}.")
            
            # Construct notification message body
            # Ensure this structure matches what notification_service expects
            message_body = {
                "user_id": user_id_for_order,
                "type": "order_update",
                "title": f"Order {order_id_from_data} Update", # More descriptive title
                "body": f"The status of your order {order_id_from_data} is now: {new_status}.",
                "data": { # Optional structured data
                    "order_id": order_id_from_data,
                    "new_status": new_status,
                    "link": f"/orders/{order_id_from_data}" 
                }
            }
            
            # Define the exchange and routing key for order update messages
            exchange_name = settings.ORDER_EVENTS_EXCHANGE
            # Routing key could be specific to the order or user, or general for order updates
            routing_key = f"order.status.{new_status.lower()}.user.{user_id_for_order}" # Example detailed routing key

            # Publish message to RabbitMQ using the corrected call
            # The publish_message function in producer.py now handles success/failure logging internally.
            await producer.publish_message(
                exchange_name=exchange_name,
                routing_key=routing_key,
                message_body=message_body
            )
            published_attempts += 1 # Count attempt to publish
            logger.info(f"Order update message queued for order {order_id_from_data}, user {user_id_for_order}.")

            # Optional: Add a small delay between messages if needed
            # await asyncio.sleep(0.1)
        # No 'else' needed here as update_mock_order_status handles non-updates by returning None

    logger.info(f"Order status check job finished. Mock orders processed for updates: {updated_count}, Notifications queued for publishing: {published_attempts}")