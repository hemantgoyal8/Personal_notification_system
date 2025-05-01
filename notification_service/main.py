import logging
import asyncio
from fastapi import FastAPI, APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from notification_service.app.api import notifications
from notification_service.app.db.database import connect_to_mongo, close_mongo_connection, create_indexes, db # Import db instance
from notification_service.app.events.consumer import start_consumer_background, stop_consumer_background, rabbitmq_connection # Import consumer functions
from notification_service.app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Notification Service",
    description="Stores and retrieves user notifications, consumes notification events.",
    version="1.0.0"
)

# Exception Handling
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"},
    )


# Include routers
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(api_router)

# Startup and Shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Notification Service...")
    # Connect to MongoDB
    connect_to_mongo()
    try:
        create_indexes() # Ensure DB indexes exist
    except Exception as e:
       logger.error(f"Could not create database indexes: {e}") # Log error but continue startup

    # Start RabbitMQ consumer in background
    # Using asyncio.create_task to run it concurrently with the FastAPI app
    logger.info("Initiating RabbitMQ consumer startup...")
    asyncio.create_task(start_consumer_background())


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Notification Service...")
    # Stop RabbitMQ consumer
    await stop_consumer_background()
    # Close MongoDB connection
    close_mongo_connection()
    logger.info("Notification Service shutdown complete.")


@app.get("/health", tags=["Health Check"])
async def health_check():
    # Check MongoDB connection
    db_status = "disconnected"
    try:
        if db.client:
            db.client.admin.command('ping') # Verify connection
            db_status = "connected"
    except Exception:
        db_status = "error"

    # Check RabbitMQ connection
    mq_status = "disconnected"
    if rabbitmq_connection and not rabbitmq_connection.is_closed:
        mq_status = "connected"
    elif rabbitmq_connection and rabbitmq_connection.is_closed:
         mq_status = "closed (reconnecting?)" # connect_robust might be retrying
    else:
        mq_status = "error/unavailable"


    return {"status": "ok", "database_status": db_status, "message_queue_status": mq_status}

# Basic root endpoint
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Notification Service"}

# To run the service (from the 'personalized-notification-system' directory):
# uvicorn notification_service.app.main:app --reload --port 8001