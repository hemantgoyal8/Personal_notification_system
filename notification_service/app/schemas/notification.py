# notification_service/app/schemas/notification.py
from pydantic import BaseModel, Field, GetJsonSchemaHandler # For Pydantic V2
from pydantic.json_schema import JsonSchemaValue # For Pydantic V2
from pydantic_core import core_schema # For Pydantic V2 validator signature
from pydantic_settings import SettingsConfigDict # For model_config
from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId # Import ObjectId

class PyObjectId(ObjectId):
    """Custom Pydantic V2 type for MongoDB ObjectId."""
    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def validate(cls, v: Any, handler: core_schema.ValidatorFunctionWrapHandler) -> ObjectId:
        """Validate that the input is a valid ObjectId or can be converted to one."""
        if isinstance(v, ObjectId):
            return v
        if ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId format")

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """
        Return JSON schema representation for PyObjectId.
        We represent it as a string in the schema.
        """
        # Use the plain string schema.
        return handler(core_schema.str_schema())
        # Or, if you want to add more details like a format:
        # json_schema = handler(core_schema.str_schema())
        # json_schema.update(format="objectid", example="507f1f77bcf86cd799439011")
        # return json_schema


# Consistent content structure
class NotificationContent(BaseModel):
    title: str
    body: str
    link: Optional[str] = None

class NotificationBase(BaseModel):
    userId: str # Assuming user ID can be any string identifier
    type: str = Field(..., example="order_update")
    content: NotificationContent
    read: bool = False
    sentAt: datetime = Field(default_factory=datetime.utcnow)

    # Pydantic V2 model configuration
    model_config = SettingsConfigDict(
        populate_by_name=True, # Replaces allow_population_by_field_name
        json_encoders={
            ObjectId: str, # Keep this if PyObjectId is used elsewhere directly
            datetime: lambda dt: dt.isoformat()
        }
    )

class NotificationCreate(NotificationBase):
    # This schema is used when creating a new notification.
    # It inherits all fields from NotificationBase.
    # The consumer will construct this from the event message.
    pass

class NotificationInDB(NotificationBase):
    # This schema represents how a notification is stored in the DB,
    # including its database ID.
    # For PostgreSQL, 'id' would typically be an int or UUID auto-generated.
    # Since you're using PostgreSQL now, PyObjectId isn't directly applicable here for the primary key.
    # Let's assume 'id' will be handled by SQLAlchemy model if this is for DB representation.
    # If this is for MongoDB still (despite overall switch to PG), then PyObjectId is relevant.
    # Given the assignment uses Postgres for notification_service, let's adjust:
    
    id: int # Assuming an integer primary key from PostgreSQL
    
    # userId was already in NotificationBase
    # type was already in NotificationBase
    # content was already in NotificationBase
    # sentAt was already in NotificationBase
    # read was already in NotificationBase

    # Pydantic V2 model configuration
    model_config = SettingsConfigDict(
        from_attributes=True,  # Replaces orm_mode for SQLAlchemy model conversion
        populate_by_name=True, # If you still need this (e.g. for _id to id mapping if it were Mongo)
        json_encoders={
            # ObjectId: str, # Only if using MongoDB somewhere with this model
            datetime: lambda dt: dt.isoformat()
        }
    )

class NotificationPublic(BaseModel):
    # This schema represents what is sent back to the client.
    # For PostgreSQL, id will likely be int then converted to str if needed by client.
    id: str # Often primary keys are exposed as strings in APIs
    userId: str
    type: str
    content: NotificationContent
    sentAt: datetime # Will be serialized by json_encoders
    read: bool

    model_config = SettingsConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )


class NotificationUpdateRead(BaseModel):
    read: bool