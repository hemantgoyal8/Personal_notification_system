from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from ..core.config import settings
# Assuming TokenPayload schema will be defined in schemas/token.py
# from user_service.app.schemas.token import TokenPayload

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# JWT Token Creation
def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode: Dict[str, Any] = {"exp": expire, "sub": str(subject)} # Ensure subject is string
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

# JWT Token Verification (Optional here, mainly for Gateway, but can be useful)
def verify_token(token: str) -> Optional[str]:
    """Verifies the token and returns the subject (user_id/email) or None if invalid."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        # If you add more data to the token, validate it using a Pydantic model here
        # try:
        #     token_data = TokenPayload(**payload)
        # except ValidationError:
        #     return None # Or raise specific exception
        
        subject = payload.get("sub")
        if subject is None:
            return None
        return subject
    except JWTError:
        return None