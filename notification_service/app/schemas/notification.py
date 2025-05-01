from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId # Import ObjectId

# Pydantic requires custom handling for ObjectId during validation/serialization
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


# Consistent content structure as requested
class NotificationContent(BaseModel):
    title: str
    body: str
    link: Optional[str] = None

class NotificationBase(BaseModel):
    userId: str # Assuming user ID is the email, like in User Service
    type: str = Field(..., example="order_update") # e.g., promotion, order_update, recommendation
    content: NotificationContent
    read: bool = False

    # Add sentAt automatically if not provided
    sentAt: datetime = Field(default_factory=datetime.utcnow)


class NotificationCreate(NotificationBase):
    # Fields inherited from NotificationBase are sufficient for creation
    # The consumer will construct this from the event message
    pass


class NotificationInDB(NotificationBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat() # Ensure datetime is ISO formatted string
        }

class NotificationPublic(BaseModel):
    id: str
    userId: str
    type: str
    content: NotificationContent
    sentAt: datetime
    read: bool

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class NotificationUpdateRead(BaseModel):
    read: bool