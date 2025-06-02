# notification_service/app/db/database.py
from pymongo import MongoClient
from pymongo.database import Database # Correct type hint
from pymongo.errors import ConnectionFailure
from ..core.config import settings, logger 
from typing import Optional, Any, Dict

class DBConnection:
    client: Optional[MongoClient] = None
    db: Optional[Database] = None # Use imported Database type

db_conn = DBConnection()

def connect_to_mongo():
    logger.info(f"Notification Service DB: Connecting to MongoDB at {settings.MONGO_URL} using database {settings.MONGO_DB_NAME}...")
    try:
        db_conn.client = MongoClient(settings.MONGO_URL, serverSelectionTimeoutMS=10000)
        db_conn.client.admin.command('ping') 
        db_conn.db = db_conn.client[settings.MONGO_DB_NAME]
        logger.info("Notification Service: Successfully connected to MongoDB.")
        create_indexes_sync() 
    except ConnectionFailure as e:
        logger.error(f"Notification Service: Could not connect to MongoDB: {settings.MONGO_URL} - {e}", exc_info=True)
        raise SystemExit(f"Notification Service: Failed to connect to MongoDB: {e}")
    except Exception as e:
        logger.error(f"Notification Service: An unexpected error occurred connecting to MongoDB: {e}", exc_info=True)
        raise SystemExit(f"Notification Service: Unexpected error connecting to MongoDB: {e}")

def close_mongo_connection(): 
    if db_conn.client:
        logger.info("Notification Service: Closing MongoDB connection...")
        db_conn.client.close()
        logger.info("Notification Service: MongoDB connection closed.")

def get_notification_collection():
    if db_conn.db is None: # Correct check
        logger.error("Notification Service: MongoDB database not initialized.")
        raise RuntimeError("Notification Service: Database not initialized.")
    return db_conn.db["notifications"]

def notification_helper(notification_doc: Dict[str, Any]) -> Dict[str, Any]:
    if notification_doc and "_id" in notification_doc:
        return {
            "id": str(notification_doc["_id"]),
            "userId": notification_doc.get("userId"),
            "type": notification_doc.get("type"),
            "content": notification_doc.get("content"),
            "sentAt": notification_doc.get("sentAt"), 
            "read": notification_doc.get("read", False)
        }
    return notification_doc if notification_doc else {}

def create_indexes_sync():
    if db_conn.db is not None: # Correct check
        logger.info("Notification Service: Creating MongoDB indexes for 'notifications' collection...")
        try:
            collection = db_conn.db["notifications"]
            collection.create_index([("userId", 1)])
            collection.create_index([("userId", 1), ("read", 1)])
            collection.create_index([("sentAt", -1)])
            logger.info("Notification Service: Indexes ensured for 'notifications' collection.")
        except Exception as e:
            logger.error(f"Notification Service: Error creating indexes: {e}", exc_info=True)
    else:
        logger.warning("Notification Service: MongoDB not connected. Skipping index creation.")