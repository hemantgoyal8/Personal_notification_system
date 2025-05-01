import logging
from fastapi import FastAPI, APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from user_service.app.api import users, auth
from user_service.app.db.database import connect_to_mongo, close_mongo_connection, create_indexes # Added index creation
from user_service.app.core.config import settings
from user_service.app.schemas.user import UserInDB 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="User Service",
    description="Manages users, authentication, and preferences.",
    version="1.0.0"
)

# Exception Handling (Example for validation errors)
from pydantic import ValidationError
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

# Include routers
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])

app.include_router(api_router)

# Startup and Shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up User Service...")
    connect_to_mongo()
    # Optional: Ensure indexes are created on startup
    # try:
    #    create_indexes() # Make sure this function exists in database.py
    # except Exception as e:
    #    logger.error(f"Could not create database indexes: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down User Service...")
    close_mongo_connection()

@app.get("/health", tags=["Health Check"])
async def health_check():
    from user_service.app.db.database import db  # Import the db instance
    # Optionally add checks for DB connection status
    try:
        # Simple check if client exists
        if db.client:
             # More robust check
             db.client.admin.command('ping')
             db_status = "connected"
        else:
             db_status = "disconnected"
    except Exception:
        db_status = "error"

    return {"status": "ok", "database_status": db_status}

# Basic root endpoint
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the User Service"}

# To run the service (from the 'personalized-notification-system' directory):
# uvicorn user_service.app.main:app --reload --port 8000