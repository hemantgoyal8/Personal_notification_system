# scheduler_service/app/main.py
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import aio_pika # For ExchangeType if declaring exchanges here
from .events import producer
from .core.config import settings, logger
from .scheduler import setup_scheduler, start_scheduler, stop_scheduler, scheduler # Ensure 'scheduler' is the APScheduler instance
from .events import producer # Import the producer module

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Scheduler service starting up (lifespan)...")
    
    # Optional: Pre-declare exchanges to ensure they exist with correct types.
    # This can also be handled by the first call to producer.publish_message if robust.
    # If doing here, ensure producer.get_rabbitmq_channel() is robust for startup.
    temp_channel = await producer.get_rabbitmq_channel()
    if temp_channel:
        try:
            logger.info(f"Declaring exchange: {settings.ORDER_EVENTS_EXCHANGE}")
            await temp_channel.declare_exchange(name=settings.ORDER_EVENTS_EXCHANGE, type=aio_pika.ExchangeType.DIRECT, durable=True)
            
            logger.info(f"Declaring exchange: {settings.PROMOTION_EVENTS_EXCHANGE}")
            await temp_channel.declare_exchange(name=settings.PROMOTION_EVENTS_EXCHANGE, type=aio_pika.ExchangeType.DIRECT, durable=True)
            
            # If you have RECOMMENDATION_EVENTS_EXCHANGE defined in settings and used:
            # logger.info(f"Declaring exchange: {settings.RECOMMENDATION_EVENTS_EXCHANGE}")
            # await temp_channel.declare_exchange(name=settings.RECOMMENDATION_EVENTS_EXCHANGE, type=aio_pika.ExchangeType.DIRECT, durable=True)
            
            logger.info("Key RabbitMQ exchanges declared/ensured on startup.")
        except Exception as e:
            logger.error(f"Failed to declare exchanges on startup: {e}", exc_info=True)
    else:
        logger.warning("RabbitMQ channel not available on startup for pre-declaration of exchanges.")

    # Pass any necessary dependencies to setup_scheduler, e.g., if jobs need settings
    # For now, assuming setup_scheduler and jobs can import settings themselves if needed
    setup_scheduler() 
    start_scheduler() # Starts APScheduler in its own thread(s)
    logger.info("APScheduler started (lifespan).")
    
    yield  # Application runs here
    
    # Code to run on shutdown
    logger.info("Scheduler service shutting down (lifespan)...")
    if scheduler and scheduler.running:
        stop_scheduler() # Stops APScheduler
        logger.info("APScheduler stopped (lifespan).")
    
    await producer.close_rabbitmq_connection() # Close RabbitMQ connection
    logger.info("RabbitMQ connection logic executed on shutdown (lifespan).")
    logger.info("Scheduler Service shutdown complete.")

app = FastAPI(
    title="Scheduler Service",
    description="Runs scheduled jobs for order updates and promotions.",
    version="1.0.0",
    lifespan=lifespan # Use the new lifespan manager
)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception in Scheduler API handler: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred in the Scheduler Service."},
    )

# API Endpoints (Minimal for Scheduler)
@app.get("/health", tags=["Health Check"])
async def health_check():
    scheduler_status = "running" if scheduler and scheduler.running else "stopped"
    
    # For mq_status, we can't easily check _rabbitmq_connection directly from producer
    # without making it accessible or having a status function in producer.
    # For simplicity, we'll just indicate it's managed by the producer.
    mq_status = "managed_by_producer (check logs for connection status)"

    jobs_info = []
    if scheduler and scheduler.running:
        try:
            for job in scheduler.get_jobs():
                 jobs_info.append({"id": job.id, "name": job.name, "next_run": str(job.next_run_time)})
        except Exception as e:
             logger.warning(f"Could not retrieve job details: {e}")
             jobs_info = "error retrieving job details"
    else:
        jobs_info = "scheduler_not_running"


    return {
        "status": "ok",
        "service": "Scheduler Service",
        "scheduler_status": scheduler_status,
        "message_queue_status": mq_status,
        "scheduled_jobs": jobs_info
    }

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Scheduler Service. This service runs background jobs."}
