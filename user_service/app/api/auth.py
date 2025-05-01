from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from user_service.app.core import security
from user_service.app.core.config import settings
from user_service.app.schemas import token as token_schema
from user_service.app.schemas import user as user_schema
from user_service.app.db import crud # Use sync crud

router = APIRouter()

@router.post("/login", response_model=token_schema.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    Uses username field for email.
    """
    user = crud.get_user_by_email_sync(email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.email, expires_delta=access_token_expires # Use email as subject
    )
    return {"access_token": access_token, "token_type": "bearer"}