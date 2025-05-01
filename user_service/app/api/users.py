from fastapi import APIRouter, HTTPException, status, Depends

from user_service.app.schemas.user import UserCreate, UserUpdate, User
from user_service.app.db import crud # Use sync crud
from user_service.app.api.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
):
    """
    Register a new user. Email must be unique.
    """
    existing_user = crud.get_user_by_email_sync(email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )
    
    user = crud.create_user_sync(user_in=user_in)
    if not user:
        # This case might occur due to unforeseen DB errors post-check
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account."
        )
        
    # Return User schema which doesn't include hashed_password
    return User.from_orm(user)


@router.get("/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    """
    Fetch details for the currently authenticated user.
    """
    # get_current_user dependency already fetches and returns the user
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update the currently authenticated user's details (name, preferences).
    """
    # We use the email from the token (in current_user) as the identifier
    updated_user = crud.update_user_sync(email=current_user.email, user_in=user_in)
    if not updated_user:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Or 500 if update failed unexpectedly
            detail="User not found or update failed."
        )
    return User.from_orm(updated_user)