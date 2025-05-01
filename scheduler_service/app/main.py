import logging
import asyncio
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from scheduler_service.app.core.config import settings, logger # Use configured logger
from scheduler_service.app.scheduler import setup_scheduler, start_scheduler, stop_scheduler, scheduler
from scheduler_service.app.events.producer import connect_to_rabbitmq, close_rabbitmq_connection, rabbitmq_connection

# Configure logging level via config if needed, but basicConfig is done in config.py
# logging.getLogger('apscheduler').setLevel(logging.WARNING) # Optional: Reduce APScheduler noise

app = FastAPI(
    title="Scheduler Service",
    description="Runs scheduled jobs for order updates and promotions.",
    version="1.0.0"
)

# Exception Handling (Optional - useful if adding more API endpoints)
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception in API handler: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"},
    )

# Startup and Shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Scheduler Service...")
    
    # Connect to RabbitMQ first (needed by jobs)
    await connect_to_rabbitmq() # Producer setup includes channel/exchange creation

    # Setup and start the scheduler
    setup_scheduler()
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Scheduler Service...")
    
    # Stop the scheduler first
    stop_scheduler()
    
    # Close RabbitMQ connection
    await close_rabbitmq_connection()
    
    logger.info("Scheduler Service shutdown complete.")

# API Endpoints (Minimal for Scheduler)
@app.get("/health", tags=["Health Check"])
async def health_check():
    # Check Scheduler status
    scheduler_status = "running" if scheduler.running else "stopped"
    
    # Check RabbitMQ connection
    mq_status = "connected" if rabbitmq_connection and not rabbitmq_connection.is_closed else "disconnected/error"

    # Check scheduled jobs status (optional, more detailed)
    jobs_status = []
    try:
        for job in scheduler.get_jobs():
             jobs_status.append({"id": job.id, "name": job.name, "next_run": str(job.next_run_time)})
    except Exception as e:
         logger.warning(f"Could not retrieve job details: {e}")
         jobs_status = "error retrieving job details"


    return {
        "status": "ok",
        "scheduler_status": scheduler_status,
        "message_queue_status": mq_status,
        "scheduled_jobs": jobs_status
    }

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Scheduler Service"}

# To run the service (from the 'personalized-notification-system' directory):
# uvicorn scheduler_service.app.main:app --reload --port 8002