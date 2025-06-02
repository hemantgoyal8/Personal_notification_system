# user_service/app/api/users.py
from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List # For UserUpdate if it returns a list or for other endpoints

# Corrected relative imports
from ..schemas.user import UserCreate, UserUpdate, User # User is the public response model
from ..db import crud 
from .deps import get_current_user # Corrected name from your repo's deps.py
from ..core.config import logger # Import logger

router = APIRouter()

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate): # Renamed from your snippet for consistency
    """
    Register a new user. Email must be unique.
    """
    # logger.info(f"API: Attempting registration for email: {user_in.email}")
    # Check if user already exists
    # get_user_by_email_sync is expected to return a UserInDB model or None
    existing_user_model = crud.get_user_by_email_sync(email=user_in.email)
    if existing_user_model:
        logger.warning(f"API: Email {user_in.email} already registered.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )
    
    # create_user_sync is expected to return a UserInDB model or None
    created_user_model = crud.create_user_sync(user_in=user_in)
    if not created_user_model:
        logger.error(f"API: Failed to create user account for {user_in.email} at CRUD level.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account."
        )
        
    # `created_user_model` is already a UserInDB instance.
    # `User` (response_model) can be created from `UserInDB` because `UserInDB` inherits from `User`'s base.
    # Pydantic will automatically handle selecting the fields for `User` from `created_user_model`.
    return created_user_model


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)): # Use UserInDB from deps if that's what it provides
    """
    Fetch details for the currently authenticated user.
    """
    return current_user # current_user from get_current_active_user is already a Pydantic model

@router.put("/me", response_model=User)
async def update_user_me(
    user_in: UserUpdate,
    current_user_from_token: User = Depends(get_current_user) # Assuming this returns User model
):
    """
    Update the currently authenticated user's details (name, preferences).
    """
    #crud.update_user_sync should expect the email/id of the user to update, and UserUpdate schema
    #It should return the updated UserInDB model or None
    updated_user_model = crud.update_user_sync(
        email=current_user_from_token.email,  # Use identifier from token
        user_update_schema=user_in
    )
    if not updated_user_model:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found or update failed."
        )
    return updated_user_model