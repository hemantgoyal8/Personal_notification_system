import strawberry
from typing import Optional, List
from datetime import datetime

# --- Input Types ---
@strawberry.input
class UserPreferencesInput:
    promotions: Optional[bool] = strawberry.UNSET
    order_updates: Optional[bool] = strawberry.UNSET
    recommendations: Optional[bool] = strawberry.UNSET

@strawberry.input
class UserRegisterInput:
    name: Optional[str] = None
    email: str
    password: str

@strawberry.input
class UserUpdateInput:
    name: Optional[str] = strawberry.UNSET
    preferences: Optional[UserPreferencesInput] = strawberry.UNSET


# --- Object Types ---
@strawberry.type
class UserPreferencesType:
    promotions: Optional[bool] = None
    order_updates: Optional[bool] = None
    recommendations: Optional[bool] = None

@strawberry.type
class UserType:
    id: str # This is the email in User Service
    email: str
    name: Optional[str] = None
    preferences: Optional[UserPreferencesType] = None

@strawberry.type
class AuthResponseType:
    access_token: str
    token_type: str

@strawberry.type
class NotificationContentType:
    title: str
    body: str
    link: Optional[str] = None

@strawberry.type
class NotificationType:
    id: str # MongoDB ObjectId as string
    userId: str
    type: str
    content: NotificationContentType
    sentAt: datetime
    read: bool

@strawberry.type
class MarkReadResponseType:
    message: str
    updated_count: int

# --- Error/Status Types (Optional but good practice) ---
@strawberry.type
class Error:
    message: str
    field: Optional[str] = None

@strawberry.type
class UpdateUserPayload:
    user: Optional[UserType] = None
    error: Optional[Error] = None