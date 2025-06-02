# user_service/app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, model_validator, AliasPath
from pydantic_settings import SettingsConfigDict # For model_config
from typing import Optional, Dict, Any
from bson import ObjectId # Import if you are dealing with ObjectId directly for _id

# Default preferences structure
DEFAULT_PREFERENCES_DICT = { # Renamed to avoid confusion with UserPreferences class
    "promotions": True,
    "order_updates": True,
    "recommendations": True
}

class UserPreferences(BaseModel):
    promotions: bool = True # Made non-optional with defaults
    order_updates: bool = True
    recommendations: bool = True

    model_config = SettingsConfigDict(extra='allow') # Or 'ignore' if you prefer

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    # Pydantic V2 handles default_factory slightly differently if the factory returns a model instance
    # It's often cleaner to initialize in a root validator or ensure the type is correct.
    # For simplicity, let's ensure preferences is always created.
    preferences: UserPreferences = Field(default_factory=UserPreferences)


class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel): # For partial updates
    name: Optional[str] = None
    preferences: Optional[UserPreferences] = None


# This class will represent data coming from MongoDB (with _id)
# and prepare it for other Pydantic models that expect 'id'.
class UserFromMongoDB(UserBase): # New helper base
    id: str = Field(validation_alias=AliasPath("_id")) # Map MongoDB '_id' to 'id' and validate

    # If _id is an ObjectId in the DB, convert it to string
    @model_validator(mode='before')
    @classmethod
    def convert_objectid_to_str(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if '_id' in data and isinstance(data['_id'], ObjectId):
                data['id'] = str(data['_id'])
                # del data['_id'] # Optionally remove _id if 'id' is the canonical field
        return data
    
    model_config = SettingsConfigDict(
        from_attributes=True,       # For creating from objects with attributes
        populate_by_name=True,      # Allows using alias field name for population
        json_encoders={ObjectId: str} # If you still deal with ObjectId directly
    )

class User(UserFromMongoDB): 
    model_config = SettingsConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class UserInDB(UserFromMongoDB): # For full user data including hashed_password, from DB
    hashed_password: str
    # Inherits 'id' (mapped from _id), email, name, preferences from UserFromMongoDB