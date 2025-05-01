from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from bson import ObjectId # Use if your IDs are ObjectIds
from typing import Optional

from user_service.app.core.security import get_password_hash
from user_service.app.schemas.user import UserCreate, UserUpdate, UserInDB
from user_service.app.db.database import get_user_collection
import logging

logger = logging.getLogger(__name__)

async def create_user(user_in: UserCreate) -> Optional[UserInDB]:
    """Creates a new user in the database."""
    collection = get_user_collection()
    hashed_password = get_password_hash(user_in.password)
    
    # Ensure preferences are set correctly on creation
    user_data = user_in.dict(exclude={"password"})
    user_data["hashed_password"] = hashed_password
    # Ensure preferences are fully populated with defaults if partial or missing
    if user_in.preferences:
         # Start with defaults, update with provided values
        prefs = {**DEFAULT_PREFERENCES, **user_in.preferences.dict(exclude_unset=True)}
        user_data["preferences"] = prefs
    else:
         user_data["preferences"] = DEFAULT_PREFERENCES

    try:
        # Using email as the document ID for uniqueness and easy lookup
        user_data["_id"] = user_in.email
        result = await collection.insert_one(user_data) # Requires Motor for await
        # If using synchronous pymongo:
        # result = collection.insert_one(user_data)
        
        # Fetch the created user to return it (using the known ID)
        created_user = await get_user_by_email(user_in.email)
        # If using synchronous pymongo:
        # created_user = get_user_by_email_sync(user_in.email) 
        return created_user
    except DuplicateKeyError:
        logger.warning(f"Attempted to create user with duplicate email: {user_in.email}")
        return None
    except Exception as e:
        logger.error(f"Error creating user {user_in.email}: {e}")
        return None # Or raise a specific exception

async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Fetches a user by their email address."""
    collection = get_user_collection()
    user_doc = await collection.find_one({"_id": email}) # Requires Motor
    # If using synchronous pymongo:
    # user_doc = collection.find_one({"_id": email}) 
    if user_doc:
        return UserInDB(**user_doc)
    return None

# Synchronous version for potential use if not using Motor
def get_user_by_email_sync(email: str) -> Optional[UserInDB]:
    """Synchronous fetch for a user by their email address."""
    collection = get_user_collection()
    user_doc = collection.find_one({"_id": email})
    if user_doc:
        return UserInDB(**user_doc)
    return None

async def update_user(email: str, user_in: UserUpdate) -> Optional[UserInDB]:
    """Updates user information (name, preferences)."""
    collection = get_user_collection()
    update_data = user_in.dict(exclude_unset=True) # Only include fields that were set

    if not update_data:
        logger.warning(f"Update called for user {email} with no data.")
        return await get_user_by_email(email) # Return current user if no update data

    # Special handling for preferences to merge, not overwrite
    if "preferences" in update_data and update_data["preferences"] is not None:
        # Fetch current preferences
        current_user = await get_user_by_email(email)
        if not current_user:
             return None # User not found
        
        current_prefs = current_user.preferences.dict() if current_user.preferences else {}
        new_prefs = update_data["preferences"] # These are already filtered by exclude_unset

        # Merge: Start with current, update with new
        merged_prefs = {**current_prefs, **new_prefs}
        update_data["preferences"] = merged_prefs


    result = await collection.update_one( # Requires Motor
        {"_id": email},
        {"$set": update_data}
    )
    # If using synchronous pymongo:
    # result = collection.update_one({"_id": email}, {"$set": update_data})

    if result.modified_count == 1 or result.matched_count == 1:
        # Return the updated user data
        updated_user = await get_user_by_email(email)
        # Sync: updated_user = get_user_by_email_sync(email)
        return updated_user
    elif result.matched_count == 0:
        logger.warning(f"Attempted to update non-existent user: {email}")
        return None # User not found
    else:
        logger.warning(f"User {email} update called but no changes made.")
        return await get_user_by_email(email) # No changes, return current state

# --- Synchronous CRUD Implementation ---
from user_service.app.schemas.user import DEFAULT_PREFERENCES # Import again

def create_user_sync(user_in: UserCreate) -> Optional[UserInDB]:
    """Creates a new user in the database (Synchronous)."""
    collection = get_user_collection()
    hashed_password = get_password_hash(user_in.password)
    
    user_data = user_in.dict(exclude={"password"})
    user_data["hashed_password"] = hashed_password
    
    # Ensure preferences are fully populated
    prefs_dict = user_in.preferences.dict(exclude_unset=True) if user_in.preferences else {}
    user_data["preferences"] = {**DEFAULT_PREFERENCES, **prefs_dict}

    try:
        user_data["_id"] = user_in.email # Using email as _id
        collection.insert_one(user_data)
        created_user = get_user_by_email_sync(user_in.email)
        return created_user
    except DuplicateKeyError:
        logger.warning(f"Attempted to create user with duplicate email: {user_in.email}")
        return None
    except Exception as e:
        logger.error(f"Error creating user {user_in.email}: {e}")
        return None

def get_user_by_email_sync(email: str) -> Optional[UserInDB]:
    """Fetches a user by their email address (Synchronous)."""
    collection = get_user_collection()
    user_doc = collection.find_one({"_id": email})
    if user_doc:
        return UserInDB(**user_doc)
    return None

def update_user_sync(email: str, user_in: UserUpdate) -> Optional[UserInDB]:
    """Updates user information (Synchronous)."""
    collection = get_user_collection()
    update_data = user_in.dict(exclude_unset=True)

    if not update_data:
        logger.warning(f"Update called for user {email} with no data.")
        return get_user_by_email_sync(email)

    if "preferences" in update_data and update_data["preferences"] is not None:
        current_user = get_user_by_email_sync(email)
        if not current_user: return None

        # Ensure current_user.preferences is treated as a dict, even if None initially
        current_prefs = current_user.preferences.dict() if current_user.preferences else DEFAULT_PREFERENCES.copy()
        
        # Get the update preferences dict, handling potential None
        new_prefs_update = update_data["preferences"] if update_data["preferences"] else {}
        
        merged_prefs = {**current_prefs, **new_prefs_update}
        update_data["preferences"] = merged_prefs # Update the dict going to MongoDB


    result = collection.update_one(
        {"_id": email},
        {"$set": update_data}
    )

    if result.modified_count >= 0 : # Check if matched or modified
        updated_user = get_user_by_email_sync(email)
        return updated_user
    else: # result.matched_count == 0
        logger.warning(f"Attempted to update non-existent user: {email}")
        return None