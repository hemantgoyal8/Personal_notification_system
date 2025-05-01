import json
import logging
import asyncio
from typing import Optional

import aio_pika
from aio_pika import ExchangeType, Message, RobustConnection

from scheduler_service.app.core.config import settings

logger = logging.getLogger(__name__)

# Global connection variable
rabbitmq_connection: Optional[RobustConnection] = None
rabbitmq_channel: Optional[aio_pika.abc.AbstractChannel] = None
rabbitmq_exchange: Optional[aio_pika.abc.AbstractExchange] = None


async def connect_to_rabbitmq() -> bool:
    """Establishes a robust connection to RabbitMQ."""
    global rabbitmq_connection
    if rabbitmq_connection and not rabbitmq_connection.is_closed:
        logger.info("RabbitMQ connection already established.")
        return True

    logger.info("Connecting to RabbitMQ for publishing...")
    try:
        loop = asyncio.get_event_loop()
        rabbitmq_connection = await aio_pika.connect_robust(
            settings.RABBITMQ_URL,
            loop=loop,
            timeout=10
        )
        rabbitmq_connection.add_close_callback(on_rabbitmq_connection_close)
        rabbitmq_connection.add_reconnect_callback(on_rabbitmq_connection_reconnect)
        logger.info("RabbitMQ connection successful.")
        # Get channel and declare exchange after connection
        await setup_rabbitmq_channel_and_exchange()
        return True
    except aio_pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Could not connect to RabbitMQ: {e}")
        rabbitmq_connection = None
        return False
    except Exception as e:
        logger.error(f"Generic error connecting to RabbitMQ: {e}")
        rabbitmq_connection = None
        return False

def on_rabbitmq_connection_close(sender, exc):
    global rabbitmq_connection, rabbitmq_channel, rabbitmq_exchange
    logger.warning(f"RabbitMQ connection closed. Exception: {exc}. Resetting channel and exchange.")
    rabbitmq_connection = None
    rabbitmq_channel = None
    rabbitmq_exchange = None

async def on_rabbitmq_connection_reconnect(sender):
    global rabbitmq_connection
    logger.info("RabbitMQ connection re-established. Setting up channel and exchange again.")
    # Re-setup channel and exchange on reconnect
    await setup_rabbitmq_channel_and_exchange()


async def setup_rabbitmq_channel_and_exchange():
    """Sets up the channel and declares the exchange."""
    global rabbitmq_channel, rabbitmq_exchange, rabbitmq_connection
    if not rabbitmq_connection or rabbitmq_connection.is_closed:
        logger.error("Cannot setup channel/exchange, RabbitMQ connection not available.")
        return False

    try:
        # Create a channel
        rabbitmq_channel = await rabbitmq_connection.channel()
        logger.info("RabbitMQ channel obtained.")

        # Declare the exchange (idempotent)
        exchange_type = ExchangeType(settings.NOTIFICATION_EXCHANGE_TYPE) # Convert string to Enum
        rabbitmq_exchange = await rabbitmq_channel.declare_exchange(
            settings.NOTIFICATION_EVENTS_EXCHANGE,
            exchange_type,
            durable=True # Make exchange survive broker restarts
        )
        logger.info(f"Declared RabbitMQ Exchange '{settings.NOTIFICATION_EVENTS_EXCHANGE}' type '{settings.NOTIFICATION_EXCHANGE_TYPE}'.")
        return True
    except Exception as e:
        logger.error(f"Error setting up RabbitMQ channel/exchange: {e}")
        rabbitmq_channel = None
        rabbitmq_exchange = None
        return False

async def publish_message(message_body: dict, routing_key: str = ""):
    """Publishes a message to the configured RabbitMQ exchange."""
    global rabbitmq_exchange, rabbitmq_channel

    if not rabbitmq_channel or rabbitmq_channel.is_closed:
        logger.warning("RabbitMQ channel is not available. Attempting to reconnect/re-setup...")
        # Attempt to re-establish connection and channel
        if await connect_to_rabbitmq():
             await setup_rabbitmq_channel_and_exchange() # Try setting up again
        
        # Check again after attempting setup
        if not rabbitmq_channel or rabbitmq_channel.is_closed:
             logger.error("Failed to publish message: RabbitMQ channel unavailable after retry.")
             return False # Indicate publish failure


    if not rabbitmq_exchange:
        logger.error("Failed to publish message: RabbitMQ exchange is not configured/available.")
        return False

    try:
        message = Message(
            body=json.dumps(message_body).encode('utf-8'),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT # Make message persistent
        )
        
        # Publish the message
        # Routing key is typically empty for FANOUT, specify for DIRECT/TOPIC
        await rabbitmq_exchange.publish(message, routing_key=routing_key)
        # logger.info(f"Published message to exchange '{settings.NOTIFICATION_EVENTS_EXCHANGE}': {message_body}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish message: {e}. Message: {message_body}", exc_info=True)
        # Handle potential channel/connection closure on error
        if isinstance(e, (aio_pika.exceptions.ChannelClosed, aio_pika.exceptions.ConnectionClosed)):
             logger.warning("Channel or connection closed during publish. Resetting state.")
             rabbitmq_channel = None
             rabbitmq_exchange = None
             # Connection reset handled by robust connection callbacks hopefully
        return False

async def close_rabbitmq_connection():
    """Closes the RabbitMQ connection."""
    global rabbitmq_connection, rabbitmq_channel
    logger.info("Closing RabbitMQ connection...")
    if rabbitmq_channel and not rabbitmq_channel.is_closed:
        try:
            await rabbitmq_channel.close()
            logger.info("RabbitMQ channel closed.")
        except Exception as e:
             logger.error(f"Error closing RabbitMQ channel: {e}")

    if rabbitmq_connection and not rabbitmq_connection.is_closed:
        try:
            await rabbitmq_connection.close()
            logger.info("RabbitMQ connection closed.")
        except Exception as e:
             logger.error(f"Error closing RabbitMQ connection: {e}")
    
    rabbitmq_connection = None
    rabbitmq_channel = None
    rabbitmq_exchange = None