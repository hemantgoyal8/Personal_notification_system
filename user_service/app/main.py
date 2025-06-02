import logging
from fastapi import FastAPI, APIRouter, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from .api import users, auth
from .db.database import connect_to_mongo, close_mongo_connection
from .core.config import settings, logger
from pydantic import ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app_lifespan: FastAPI): 
    logger.info("Starting up User Service (lifespan)...")
    connect_to_mongo() # This function internally calls create_indexes_sync()
    yield
    logger.info("Shutting down User Service (lifespan)...")
    close_mongo_connection()


app = FastAPI(
    title="User Service",
    description="Manages users, authentication, and preferences.",
    version="1.0.0",
    lifespan=lifespan
)

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"Pydantic ValidationError: {exc.errors()}", exc_info=False)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

# Include routers
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(api_router)

@app.get("/health", tags=["Health Check"])
async def health_check():
    from .db.database import client as mongo_client
    db_status = "disconnected"
    try:
        if mongo_client:
             # More robust check
             mongo_client.admin.command('ping')
             db_status = "connected"
        else:
             db_status = "disconnected"
    except Exception as e:
        logger.error(f"Health check: DB ping failed: {e}")
        db_status = "error"

    return {"status": "ok", "service":"User Service", "database_status": db_status}

# Basic root endpoint
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the User Service"}
