# notification_service/main.py
import logging
import asyncio
from fastapi import FastAPI, APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from contextlib import asynccontextmanager
from typing import Optional

# Corrected relative imports
from app.api.notifications import router as notifications_api_router # Assuming 'router' is defined in notifications.py
from app.db.database import connect_to_mongo, close_mongo_connection, create_indexes_sync # Import the SYNC version
from app.events import consumer
from app.core.config import settings, logger 

_background_consumer_task: Optional[asyncio.Task] = None

# app = FastAPI(...) # Will be defined later with lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _background_consumer_task
    logger.info("Starting up Notification Service (lifespan)...")
    # Connect to MongoDB (which also calls create_indexes_sync internally)
    connect_to_mongo() 
    # create_indexes_sync() # No longer needed here, called by connect_to_mongo

    logger.info("Initiating RabbitMQ consumer startup (lifespan)...")
    consumer_task = asyncio.create_task(consumer.start_consuming())
    
    yield # Application runs here
    
    logger.info("Shutting down Notification Service (lifespan)...")
    # Stop RabbitMQ consumer (if stop_consuming is implemented and needed for graceful shutdown)
    if hasattr(consumer, 'stop_consuming'): # Check if the function exists
        logger.info("Attempting to stop consumer task...")
        await consumer.stop_consuming(consumer_task) # Pass the task to cancel it
    else:
        # If no explicit stop, try cancelling the task directly if stored
        if 'consumer_task' in locals() and consumer_task and not consumer_task.done():
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                logger.info("Consumer task cancelled.")

    # Close MongoDB connection
    close_mongo_connection()
    logger.info("Notification Service shutdown complete.")

app = FastAPI(
    title="Notification Service",
    description="Stores and retrieves user notifications, consumes notification events.",
    version="1.0.0",
    lifespan=lifespan
)

# Exception Handling
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"Pydantic ValidationError: {exc.errors()}", exc_info=False)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception in Notification Service: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred in Notification Service"},
    )

# Include routers
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(notifications_api_router, prefix="/notifications", tags=["Notifications"])
app.include_router(api_router)


@app.get("/health", tags=["Health Check"])
async def health_check():
    from app.db.database import db_conn as mongo_db_connection_wrapper # Import the wrapper
    
    db_status = "disconnected"
    try:
        # Check if client exists on the wrapper and then ping
        if mongo_db_connection_wrapper.client: 
            mongo_db_connection_wrapper.client.admin.command('ping')
            db_status = "connected"
    except Exception as e:
        logger.warning(f"Health check: DB ping failed: {e}")
        db_status = "error_pinging"

    # For RabbitMQ, it's harder to get a live status from an external module's internal connection
    # without a dedicated status function in consumer.py.
    # We can assume if the consumer task is running, it's trying.
    # This is a simplified check.
    mq_status = "consumer_active (check logs for actual connection status)"
    # You could add a global flag in consumer.py that start_consuming sets/unsets.

    return {"status": "ok", "service": "Notification Service", "database_status": db_status, "message_queue_status": mq_status}

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Notification Service"}