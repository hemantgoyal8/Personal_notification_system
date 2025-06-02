# user_service/app/db/database.py
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.database import Database
from typing import Optional
from ..core.config import settings, logger # Ensure logger is imported

client: Optional[MongoClient] = None
db_instance: Optional[Database] = None # To store the database object

def connect_to_mongo():
    global client, db_instance
    logger.info(f"User Service DB: Connecting to MongoDB at {settings.MONGO_URL} with DB {settings.MONGO_DB_NAME}...")
    try:
        client = MongoClient(settings.MONGO_URL, serverSelectionTimeoutMS=10000)
        client.admin.command('ping') # Verify connection
        db_instance = client[settings.MONGO_DB_NAME] # Get the database object
        logger.info("User Service: Successfully connected to MongoDB.")
        # Call create_indexes after successful connection
        create_indexes_sync() # Call the synchronous version
    except ConnectionFailure as e:
        logger.error(f"User Service: Could not connect to MongoDB: {e}", exc_info=True)
        raise SystemExit(f"User Service: Failed to connect to MongoDB: {e}")
    except Exception as e:
        logger.error(f"User Service: Unexpected error connecting to MongoDB: {e}", exc_info=True)
        raise SystemExit(f"User Service: Unexpected error connecting to MongoDB: {e}")

def close_mongo_connection():
    global client
    if client:
        logger.info("User Service: Closing MongoDB connection...")
        client.close()
        logger.info("User Service: MongoDB connection closed.")

def get_database(): # This now returns the stored db_instance
    if db_instance is None:
        # This indicates connect_to_mongo wasn't called or failed.
        # Should be handled by application lifecycle.
        logger.error("User Service: Database not initialized. connect_to_mongo must be called first.")
        raise RuntimeError("User Service: Database not initialized.")
    return db_instance

def get_user_collection():
    database = get_database()
    return database["users"] 

def create_indexes_sync(): 
    if db_instance is not None:
        logger.info("User Service: Creating MongoDB indexes for 'users' collection...")
        try:
            users_collection = db_instance["users"]
            users_collection.create_index("email", unique=True)
            logger.info("User Service: Indexes created successfully for 'users' collection.")
        except Exception as e:
            logger.error(f"User Service: Error creating MongoDB indexes: {e}", exc_info=True)
    else:
        logger.warning("User Service: MongoDB not connected. Skipping index creation.")