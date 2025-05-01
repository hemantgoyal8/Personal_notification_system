from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from notification_service.app.core.config import settings
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)

class MongoDB:
    client: MongoClient = None

db = MongoDB()

def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    try:
        db.client = MongoClient(
            settings.MONGO_DETAILS,
            serverSelectionTimeoutMS=5000 # Timeout after 5 seconds
        )
        # The ismaster command is cheap and does not require auth.
        db.client.admin.command('ismaster')
        logger.info("MongoDB connection successful.")
        database = db.client[settings.DATABASE_NAME]
        return database
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise SystemExit(f"Failed to connect to MongoDB: {e}")

def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed.")

def get_database():
    if db.client is None:
        logger.warning("MongoDB client is not initialized. Attempting connection.")
        return connect_to_mongo()
    try:
        # Verify connection before returning
        db.client.admin.command('ping')
        return db.client[settings.DATABASE_NAME]
    except ConnectionFailure as e:
         logger.error(f"MongoDB connection lost: {e}. Attempting reconnect...")
         return connect_to_mongo() # Attempt to reconnect


def get_notification_collection():
    database = get_database()
    return database.notifications

def create_indexes():
    """Creates necessary indexes for the notifications collection."""
    try:
        collection = get_notification_collection()
        collection.create_index([("userId", 1), ("sentAt", -1)]) # Index for fetching user's notifications sorted
        collection.create_index([("userId", 1), ("read", 1)]) # Index for fetching unread notifications
        logger.info("Notification collection indexes ensured.")
    except Exception as e:
        logger.error(f"Error creating indexes for notifications collection: {e}")

# Helper to convert MongoDB document _id (ObjectId) to string
def notification_helper(notification) -> dict:
    return {
        "id": str(notification["_id"]),
        "userId": notification["userId"],
        "type": notification["type"],
        "content": notification["content"],
        "sentAt": notification["sentAt"],
        "read": notification["read"],
    }