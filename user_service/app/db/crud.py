# user_service/app/db/crud.py
from pymongo.errors import DuplicateKeyError # Import this
from typing import Optional, Dict, Any
from passlib.context import CryptContext # Assuming this is where get_password_hash comes from

# Corrected relative imports
from .database import get_user_collection # From your synchronous database.py
from ..schemas.user import UserCreate, UserInDB, DEFAULT_PREFERENCES_DICT # Import UserInDB and DEFAULT_PREFERENCES_DICT
from ..core.security import get_password_hash # Assuming this is where it is
from ..core.config import logger # Import logger

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # Defined in core.security.py

def get_user_by_email_sync(email: str) -> Optional[UserInDB]: # Returns Pydantic model or None
    """Fetches a user by email from MongoDB."""
    users_collection = get_user_collection()
    user_doc = users_collection.find_one({"email": email}) # Or {"_id": email} if email is the _id
    if user_doc:
        # The UserFromMongoDB (parent of UserInDB) handles _id to id conversion
        # and other necessary transformations via model_validate.
        try:
            return UserInDB.model_validate(user_doc)
        except Exception as e:
            logger.error(f"Error validating user data from DB for email {email}: {e}", exc_info=True)
            return None
    return None

def create_user_sync(user_in: UserCreate) -> Optional[UserInDB]: # Returns Pydantic model or None
    """Creates a new user in the database (synchronous)."""
    users_collection = get_user_collection()
    hashed_password = get_password_hash(user_in.password)
    
    preferences_data = DEFAULT_PREFERENCES_DICT.copy() # Start with defaults
    if user_in.preferences:
        # Pydantic V2: user_in.preferences.model_dump(exclude_unset=True)
        preferences_data.update(user_in.preferences.model_dump(exclude_unset=True))

    user_doc_to_insert = {
        "_id": user_in.email,  # Using email as _id
        "email": user_in.email,
        "name": user_in.name,
        "hashed_password": hashed_password,
        "preferences": preferences_data,
        # Add other fields from UserCreate or UserBase as needed
    }

    try:
        users_collection.insert_one(user_doc_to_insert)
        # Fetch the created user to return it with all transformations (like _id to id)
        # We search by email which is the _id here
        created_user_doc_from_db = users_collection.find_one({"_id": user_in.email})
        if created_user_doc_from_db:
            return UserInDB.model_validate(created_user_doc_from_db) # Convert to Pydantic model
        return None # Should not happen if insert was successful
    except DuplicateKeyError:
        logger.warning(f"Attempted to create user with duplicate email (which is _id): {user_in.email}")
        # This will be caught by the pre-check in the API route, but good to have DB level safety
        return None 
    except Exception as e:
        logger.error(f"Error creating user {user_in.email} in DB: {e}", exc_info=True)
        return None