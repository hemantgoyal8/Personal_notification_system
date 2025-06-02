# notification_service/app/events/consumer.py
import asyncio
import aio_pika
import json
from typing import Optional

from ..core.config import settings, logger
from ..db import crud # Assuming synchronous CRUD for now
from ..schemas.notification import NotificationCreate, NotificationContent # Ensure correct Pydantic models
from pydantic import ValidationError

# Global variable to hold the main consumer task
_consumer_task: Optional[asyncio.Task] = None

async def _process_message(message: aio_pika.IncomingMessage):
    """
    Internal callback function to process messages received from RabbitMQ.
    """
    async with message.process(requeue=False): # Auto-ack on success, auto-nack on exception if requeue=False
        try:
            raw_body = message.body.decode('utf-8')
            logger.info(f"Consumer received raw message: {raw_body}")
            data = json.loads(raw_body)

            # Basic validation for required top-level keys
            required_keys = ['userId', 'type', 'content']
            if not all(k in data for k in required_keys):
                logger.error(f"Missing required fields in message: {data}. Skipping.")
                return

            content_data = data.get('content', {})
            if not isinstance(content_data, dict) or not all(k in content_data for k in ['title', 'body']):
                logger.error(f"Invalid 'content' structure: {content_data} in message: {data}. Skipping.")
                return

            # Create Pydantic models
            notification_content = NotificationContent(
                title=content_data.get('title'),
                body=content_data.get('body'),
                link=content_data.get('link') 
            )
            
            notification_to_create = NotificationCreate(
                userId=str(data.get('userId')), # Ensure userId is string
                type=data.get('type'),
                content=notification_content
            )

            logger.info(f"Attempting to store notification for user: {notification_to_create.userId}, type: {notification_to_create.type}")
            
            # Assuming crud.create_notification is synchronous
            # If it were async, you would await it.
            # In a real async app, you might use run_in_threadpool for sync DB operations.
            created_notification = crud.create_notification(notification_in=notification_to_create)

            if created_notification:
                logger.info(f"Successfully stored notification ID {created_notification.id} for user {created_notification.userId}")
            else:
                logger.error(f"Failed to store notification for user {notification_to_create.userId}. This message will be NACKed implicitly by raising error.")
                raise RuntimeError("Failed to store notification in DB, message will be NACKed.") # Will NACK

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON message: {message.body}", exc_info=True)
            raise # Re-raise to NACK the message
        except ValidationError as e:
            logger.error(f"Message validation failed: {e}. Raw message: {message.body.decode()}", exc_info=True)
            raise # Re-raise to NACK the message
        except Exception as e:
            logger.error(f"Unhandled error processing message: {e}. Raw message: {message.body.decode()}", exc_info=True)
            raise # Re-raise to NACK the message


async def _run_consumer_logic():
    """The core logic for connecting, declaring, and consuming messages."""
    connection: Optional[aio_pika.RobustConnection] = None
    try:
        logger.info(f"Consumer logic: Attempting robust connection to RabbitMQ at {settings.RABBITMQ_URL}")
        # RobustConnection will handle retries for connecting internally
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL, timeout=settings.RABBITMQ_CONNECT_TIMEOUT or 30)
        
        async with connection: # Use connection as a context manager
            logger.info("Consumer logic: Successfully connected to RabbitMQ.")
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=settings.RABBITMQ_CONSUMER_PREFETCH_COUNT or 10)

            logger.info(f"Consumer logic: Declaring exchange '{settings.NOTIFICATION_EVENTS_EXCHANGE}' (type: {settings.NOTIFICATION_EXCHANGE_TYPE}, durable: True)")
            exchange_type = getattr(aio_pika.ExchangeType, settings.NOTIFICATION_EXCHANGE_TYPE.upper(), aio_pika.ExchangeType.FANOUT)
            exchange = await channel.declare_exchange(
                settings.NOTIFICATION_EVENTS_EXCHANGE, 
                exchange_type,
                durable=True
            )
            
            logger.info(f"Consumer logic: Declaring queue '{settings.NOTIFICATION_QUEUE}' (durable: True)")
            queue = await channel.declare_queue(settings.NOTIFICATION_QUEUE, durable=True)
            
            logger.info(f"Consumer logic: Binding queue '{settings.NOTIFICATION_QUEUE}' to exchange '{settings.NOTIFICATION_EVENTS_EXCHANGE}' with binding key '{settings.BINDING_KEY or ""}'")
            await queue.bind(exchange, routing_key=settings.BINDING_KEY or "") 
            
            logger.info(f"Consumer logic: Starting to consume from queue '{settings.NOTIFICATION_QUEUE}'")
            await queue.consume(_process_message)
            
            logger.info(" [*] Consumer is waiting for messages. This task will run indefinitely until cancelled.")
            await asyncio.Future() # Keep this coroutine alive until cancelled

    except asyncio.CancelledError:
        logger.info("Consumer logic task was cancelled.")
    except Exception as e:
        logger.error(f"Major error in consumer logic (e.g., initial connection failed after retries): {e}", exc_info=True)
        # If RobustConnection fails all its retries, it raises.
        # This task might exit, and start_consuming might try to restart it.
        raise # Re-raise to let the manager know this attempt failed critically
    finally:
        if connection and not connection.is_closed:
            await connection.close()
            logger.info("Consumer logic: RabbitMQ connection closed in finally block.")


async def start_consuming(): # This is the function main.py will call
    """Starts the RabbitMQ consumer logic as a background task if not already running."""
    global _consumer_task
    if _consumer_task and not _consumer_task.done():
        logger.info("Consumer task is already running.")
        return

    logger.info("Starting RabbitMQ consumer background task...")
    # We wrap _run_consumer_logic in another task that can retry starting it
    async def supervised_consumer_run():
        retry_delay = 5
        max_retries = 3 # Example: limit initial startup retries
        attempt = 0
        while True:
            try:
                await _run_consumer_logic()
                logger.info("Consumer logic exited normally (should not happen if using asyncio.Future()).")
                break # Exit supervisor if _run_consumer_logic exits normally
            except asyncio.CancelledError:
                logger.info("Supervised consumer run cancelled.")
                break
            except Exception as e:
                attempt +=1
                logger.error(f"Consumer logic failed critically (attempt {attempt}): {e}. Retrying in {retry_delay}s if attempts < {max_retries}.")
                if attempt >= max_retries:
                    logger.error("Max retries reached for starting consumer logic. Giving up.")
                    break
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60) # Exponential backoff up to 60s

    _consumer_task = asyncio.create_task(supervised_consumer_run())
    logger.info(f"Consumer background task created: {_consumer_task.get_name()}")


async def stop_consuming(task: Optional[asyncio.Task] = None): # main.py can pass the task
    """Stops the RabbitMQ consumer task."""
    global _consumer_task
    task_to_stop = task or _consumer_task # Prefer passed task, fallback to global
    
    if task_to_stop and not task_to_stop.done():
        logger.info(f"Attempting to stop/cancel consumer task: {task_to_stop.get_name()}")
        task_to_stop.cancel()
        try:
            await task_to_stop
            logger.info(f"Consumer task {task_to_stop.get_name()} awaited after cancellation.")
        except asyncio.CancelledError:
            logger.info(f"Consumer task {task_to_stop.get_name()} successfully cancelled.")
        except Exception as e:
            logger.error(f"Error during consumer task {task_to_stop.get_name()} cancellation/await: {e}", exc_info=True)
    else:
        logger.info("Consumer task not running or already stopped/cancelled.")
    
    if task_to_stop == _consumer_task: # If we stopped the global one, clear it
        _consumer_task = None