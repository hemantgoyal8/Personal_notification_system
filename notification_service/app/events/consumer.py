import asyncio
import json
import logging
from typing import Optional

import aio_pika
from aio_pika import IncomingMessage, RobustConnection, ExchangeType
from pydantic import ValidationError

from notification_service.app.core.config import settings
from notification_service.app.schemas.notification import NotificationCreate, NotificationContent
from notification_service.app.db import crud # Using sync crud for now

logger = logging.getLogger(__name__)

async def process_notification_event(message: IncomingMessage):
    """Callback function to process messages received from RabbitMQ."""
    async with message.process(requeue=False): # Auto-ack if processing succeeds, don't requeue by default
        try:
            data = json.loads(message.body.decode('utf-8'))
            logger.info(f"Received raw message: {data}")

            # Validate required fields
            if not all(k in data for k in ('userId', 'type', 'content')):
                 logger.error(f"Missing required fields in message: {data}")
                 # Explicitly nack and don't requeue (or send to DLQ if configured)
                 # await message.nack(requeue=False) # process context does this on exception
                 return # Skip processing

            # Further validation for content structure
            content_data = data.get('content', {})
            if not isinstance(content_data, dict) or not all(k in content_data for k in ('title', 'body')):
                 logger.error(f"Invalid 'content' structure in message: {content_data}")
                 return # Skip processing

            # Create NotificationContent object
            notification_content = NotificationContent(
                title=content_data.get('title'),
                body=content_data.get('body'),
                link=content_data.get('link') # Optional
            )
            
            # Create NotificationCreate object
            notification_data = NotificationCreate(
                userId=data.get('userId'),
                type=data.get('type'),
                content=notification_content
                # sentAt and read have defaults
            )

            logger.info(f"Attempting to store notification for user: {notification_data.userId}")

            
            # Direct synchronous call (simpler for now, blocks):
            created_notification = crud.create_notification_sync(notification_data)

            if created_notification:
                logger.info(f"Successfully stored notification ID {created_notification.id} for user {created_notification.userId}")
                # Message is automatically acked by `message.process()` context manager if no exception
            else:
                logger.error(f"Failed to store notification for user {notification_data.userId}. Message will be NACKed.")
                # Raise an exception to trigger NACK from the context manager
                raise RuntimeError("Failed to store notification in DB")

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON message: {message.body}")
            # Let context manager handle NACK
            raise
        except ValidationError as e:
            logger.error(f"Message validation failed: {e}. Message: {message.body.decode()}")
            # Let context manager handle NACK
            raise
        except Exception as e:
            logger.error(f"Unhandled error processing message: {e}")

async def consume_notifications(connection: RobustConnection) -> Optional[aio_pika.abc.AbstractChannel]:
    """Sets up the RabbitMQ consumer."""
    if not connection or connection.is_closed:
        logger.error("RabbitMQ connection is not available.")
        return None

    try:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10) # Process up to 10 messages concurrently

        # Declare the exchange (idempotent)
        exchange = await channel.declare_exchange(
            settings.NOTIFICATION_EVENTS_EXCHANGE,
            ExchangeType.FANOUT, # Or DIRECT/TOPIC depending on producer setup
            durable=True
        )

        # Declare the queue (idempotent)
        queue = await channel.declare_queue(
            settings.NOTIFICATION_QUEUE,
            durable=True # Ensure queue survives broker restarts
            # arguments={"x-dead-letter-exchange": "dlx_exchange_name"} # Optional DLQ setup
        )

        # Bind the queue to the exchange
        await queue.bind(exchange, routing_key=settings.BINDING_KEY) # Use configured binding key

        logger.info(f"Declared Exchange '{settings.NOTIFICATION_EVENTS_EXCHANGE}', Queue '{settings.NOTIFICATION_QUEUE}'")
        logger.info(f"[*] Waiting for messages in queue '{settings.NOTIFICATION_QUEUE}'. To exit press CTRL+C")

        # Start consuming messages
        await queue.consume(process_notification_event)
        
        return channel # Return the channel so it can be potentially managed/closed later

    except aio_pika.exceptions.AMQPConnectionError as e:
        logger.error(f"AMQP Connection Error during consumer setup: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to setup RabbitMQ consumer: {e}")
        # Potentially attempt retry logic here or in the connection setup
        return None

# Global variable to hold the consumer task
consumer_task = None
rabbitmq_connection = None
rabbitmq_channel = None

async def connect_to_rabbitmq() -> Optional[RobustConnection]:
    global rabbitmq_connection
    logger.info("Connecting to RabbitMQ...")
    try:
        # Ensure event loop is running, useful if called outside async context sometimes
        loop = asyncio.get_event_loop() 
        connection = await aio_pika.connect_robust(
            settings.RABBITMQ_URL,
            loop=loop,
            timeout=10 # Connection timeout
        )
        logger.info("RabbitMQ connection successful.")
        rabbitmq_connection = connection
        
        # Add connection lost callback for monitoring/reconnection logic
        connection.add_close_callback(on_rabbitmq_connection_close)
        connection.add_reconnect_callback(on_rabbitmq_connection_reconnect)

        return connection
    except aio_pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Could not connect to RabbitMQ after multiple attempts: {e}")
        rabbitmq_connection = None
        return None # Allow startup to continue, maybe retry later
    except Exception as e:
        logger.error(f"Generic error connecting to RabbitMQ: {e}")
        rabbitmq_connection = None
        return None


def on_rabbitmq_connection_close(sender, exc):
    global rabbitmq_connection
    logger.warning(f"RabbitMQ connection closed. Exception: {exc}")
    rabbitmq_connection = None # Mark connection as lost

def on_rabbitmq_connection_reconnect(sender):
    global rabbitmq_connection
    logger.info("RabbitMQ connection re-established.")
    # We might need to restart consumers if they weren't robustly handled by the channel/connection
    # For now, assume connect_robust handles restarting consumers on the channel.


async def start_consumer_background():
    """Connects to RabbitMQ and starts the consumer in the background."""
    global consumer_task, rabbitmq_connection, rabbitmq_channel
    
    # Check if already running
    if consumer_task and not consumer_task.done():
         logger.info("Consumer task already running.")
         return

    connection = await connect_to_rabbitmq()
    if connection:
        rabbitmq_channel = await consume_notifications(connection)
        if rabbitmq_channel:
            logger.info("RabbitMQ Consumer setup complete and running.")
           
            consumer_task = asyncio.create_task
        else:
             logger.error("Failed to start RabbitMQ consumer.")
             # No need to close connection here, connect_robust handles retries
    else:
        logger.error("Failed to establish RabbitMQ connection for consumer.")
        # Implement retry logic if needed, e.g., using asyncio.sleep and recalling start_consumer_background


async def stop_consumer_background():
    """Stops the RabbitMQ consumer and closes connection."""
    global consumer_task, rabbitmq_connection, rabbitmq_channel
    logger.info("Stopping RabbitMQ consumer...")

  
    if consumer_task and not consumer_task.done():
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Consumer task cancelled.")

    if rabbitmq_channel and not rabbitmq_channel.is_closed:
        try:
            await rabbitmq_channel.close()
            logger.info("RabbitMQ channel closed.")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ channel: {e}")
        rabbitmq_channel = None

    if rabbitmq_connection and not rabbitmq_connection.is_closed:
        try:
            await rabbitmq_connection.close()
            logger.info("RabbitMQ connection closed.")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
        rabbitmq_connection = None

    consumer_task = None # Reset task variable