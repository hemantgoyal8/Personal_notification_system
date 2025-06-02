# scheduler_service/app/events/producer.py
import asyncio
import aio_pika
import json
from typing import Optional
from ..core.config import settings, logger # Ensure logger is correctly imported/defined

class RabbitMQProducer:
    def __init__(self, rabbitmq_url: Optional[str] = None):
        self.rabbitmq_url = rabbitmq_url or settings.RABBITMQ_URL
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._is_connecting = asyncio.Lock() # To prevent multiple concurrent connection attempts

    async def connect(self):
        """Establishes a robust connection and channel to RabbitMQ."""
        async with self._is_connecting: # Ensure only one coroutine tries to connect at a time
            if self._channel and not self._channel.is_closed:
                logger.debug("RabbitMQ channel already active.")
                return

            try:
                logger.info(f"Attempting to connect to RabbitMQ at {self.rabbitmq_url}...")
                if self._connection is None or self._connection.is_closed:
                    self._connection = await aio_pika.connect_robust(self.rabbitmq_url)
                    logger.info("Successfully connected to RabbitMQ.")
                
                self._channel = await self._connection.channel()
                logger.info("Successfully obtained RabbitMQ channel.")
            except Exception as e:
                logger.error(f"Error connecting to RabbitMQ or getting channel: {e}", exc_info=True)
                # Reset on significant error to force full reconnect next time
                if self._channel and not self._channel.is_closed: await self._channel.close()
                if self._connection and not self._connection.is_closed: await self._connection.close()
                self._channel = None
                self._connection = None
                raise # Re-raise the exception so the caller knows connection failed

    async def send_message(self, exchange_name: str, routing_key: str, message_body: dict):
        """
        Publishes a message to the specified RabbitMQ exchange.
        Ensures connection and channel are active.
        """
        if self._channel is None or self._channel.is_closed:
            logger.warning("RabbitMQ channel not available for send_message. Attempting to connect...")
            await self.connect() # Attempt to reconnect/re-establish channel
            if self._channel is None or self._channel.is_closed: # Check again after attempt
                logger.error(f"Still cannot send message, RabbitMQ channel unavailable for exchange '{exchange_name}'.")
                raise ConnectionError("RabbitMQ channel unavailable after attempting to connect.")


        try:
            logger.debug(f"Declaring exchange: '{exchange_name}' (type: DIRECT, durable: True)")
            exchange = await self._channel.declare_exchange(
                name=exchange_name,
                type=aio_pika.ExchangeType.DIRECT, # Or TOPIC, FANOUT
                durable=True
            )
            
            message_json = json.dumps(message_body)
            message = aio_pika.Message(
                body=message_json.encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            logger.info(f"Publishing message to exchange '{exchange_name}', routing_key '{routing_key}'")
            await exchange.publish(message, routing_key=routing_key)
            logger.debug(f"Message published successfully to '{exchange_name}' with key '{routing_key}'.")
            return True # Indicate success
        except Exception as e:
            logger.error(f"Failed to publish message to '{exchange_name}': {e}", exc_info=True)
            return False # Indicate failure

    async def close(self):
        """Closes the RabbitMQ channel and connection."""
        closed_something = False
        if self._channel and not self._channel.is_closed:
            try:
                await self._channel.close()
                logger.info("RabbitMQ channel closed by producer instance.")
                closed_something = True
            except Exception as e:
                logger.error(f"Error closing RabbitMQ channel in producer instance: {e}", exc_info=True)
        
        if self._connection and not self._connection.is_closed:
            try:
                await self._connection.close()
                logger.info("RabbitMQ connection closed by producer instance.")
                closed_something = True
            except Exception as e:
                logger.error(f"Error closing RabbitMQ connection in producer instance: {e}", exc_info=True)
        
        if closed_something:
            self._connection = None
            self._channel = None

# --- Standalone functions for other jobs if they don't use the class ---
# You might choose to have ALL jobs use the RabbitMQProducer class,
# or keep these standalone functions if order_updates and promotions prefer them.
# If you keep these, they need their own connection management or to use a shared producer instance.

_standalone_producer_instance: Optional[RabbitMQProducer] = None
_standalone_producer_lock = asyncio.Lock()

async def get_standalone_producer() -> RabbitMQProducer:
    """Gets a shared instance of RabbitMQProducer."""
    global _standalone_producer_instance
    async with _standalone_producer_lock:
        if _standalone_producer_instance is None:
            _standalone_producer_instance = RabbitMQProducer()

        if _standalone_producer_instance._channel is None or _standalone_producer_instance._channel.is_closed:
            try:
                await _standalone_producer_instance.connect()
            except Exception as e:
                logger.error(f"Failed to connect standalone producer: {e}")
                # Don't return it if connection failed
                raise ConnectionError(f"Failed to connect standalone producer: {e}") from e
    return _standalone_producer_instance

async def get_rabbitmq_channel() -> Optional[aio_pika.Channel]: # RE-ADD THIS FUNCTION
    """Convenience function to get the channel from the standalone producer."""
    try:
        producer_instance = await get_standalone_producer()
        return producer_instance._channel # Access the channel directly
    except ConnectionError:
        return None # If producer couldn't connect
    except Exception as e:
        logger.error(f"Error obtaining channel via get_rabbitmq_channel: {e}", exc_info=True)
        return None
            

async def publish_message(exchange_name: str, routing_key: str, message_body: dict) -> bool:
    """Standalone publish_message function using a shared producer instance."""
    try:
        producer_instance = await get_standalone_producer()
        return await producer_instance.send_message(exchange_name, routing_key, message_body)
    except ConnectionError: # Raised by producer.send_message if channel is unavailable
        logger.error(f"ConnectionError in standalone publish_message for {exchange_name}/{routing_key}.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in standalone publish_message: {e}", exc_info=True)
        return False

async def close_rabbitmq_connection(): # This would close the shared standalone instance
    """Closes the shared standalone producer instance's connection."""
    global _standalone_producer_instance
    if _standalone_producer_instance:
        logger.info("Closing standalone RabbitMQ producer connection...")
        await _standalone_producer_instance.close()
        _standalone_producer_instance = None