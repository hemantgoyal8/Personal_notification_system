from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from user_service.app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: MongoClient = None

db = MongoDB()

def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    try:
        db.client = MongoClient(settings.MONGO_DETAILS)
        # The ismaster command is cheap and does not require auth.
        db.client.admin.command('ismaster')
        logger.info("MongoDB connection successful.")
        # Get the database
        database = db.client[settings.DATABASE_NAME]
        return database
    except ConnectionFailure as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise SystemExit(f"Failed to connect to MongoDB: {e}") # Exit if DB connection fails on startup

def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed.")

def get_database():
    if db.client is None:
        # This case might happen if called before connect_to_mongo or after close_mongo_connection
        # In a FastAPI context with dependencies or startup/shutdown events, this shouldn't be common
        logger.warning("MongoDB client is not initialized. Attempting connection.")
        return connect_to_mongo()
    return db.client[settings.DATABASE_NAME]

def get_user_collection():
    database = get_database()
    return database.users
