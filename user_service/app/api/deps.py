from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import ValidationError
from typing import Optional

from ..core import security
from ..core.config import settings
from ..schemas.token import TokenPayload
from ..schemas.user import User # We need the User schema
from ..db import crud # Use the synchronous crud for now

# Define the OAuth2 scheme pointing to the login endpoint
# The tokenUrl should be the path to your login endpoint relative to the root
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    subject = security.verify_token(token)
    if subject is None:
        raise credentials_exception
    
    # Assuming subject is the user's email which is the ID
    user = crud.get_user_by_email_sync(email=subject)
    if user is None:
        raise credentials_exception
        
    # Return the user data excluding sensitive info like hashed_password
    # The crud function returns UserInDB, let's convert to User (which excludes password)
    return User.from_orm(user)

# Dependency for optional user (e.g., for public endpoints that behave differently if logged in)
async def get_optional_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    if token is None:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None