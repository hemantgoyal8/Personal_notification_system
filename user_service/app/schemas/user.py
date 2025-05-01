from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any

# Default preferences structure
DEFAULT_PREFERENCES = {
    "promotions": True,
    "order_updates": True,
    "recommendations": True
}

class UserPreferences(BaseModel):
    promotions: Optional[bool] = True
    order_updates: Optional[bool] = True
    recommendations: Optional[bool] = True

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    preferences: Optional[UserPreferences] = Field(default_factory=lambda: UserPreferences(**DEFAULT_PREFERENCES))

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    preferences: Optional[UserPreferences] = None # Allow partial updates

class UserInDBBase(UserBase):
    id: str = Field(alias="_id") # Map MongoDB's _id to id

    class Config:
        orm_mode = True
        allow_population_by_field_name = True # Allow using '_id' when creating instance
        json_encoders = {
            # If you store id as ObjectId, you might need this:
            # ObjectId: str
        }

class User(UserInDBBase):
    pass # Inherits all fields from UserInDBBase

class UserInDB(UserInDBBase):
    hashed_password: str