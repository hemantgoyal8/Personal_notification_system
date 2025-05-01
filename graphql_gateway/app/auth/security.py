import logging
from typing import Optional

from jose import JWTError, jwt
from graphql_gateway.app.core.config import settings

logger = logging.getLogger(__name__)

def verify_token(token: str) -> Optional[str]:
    """
    Verifies the JWT token and returns the subject (user_id/email) if valid.
    Returns None if the token is invalid or expired.
    """
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        subject: Optional[str] = payload.get("sub")
        if subject is None:
            logger.warning("Token verification failed: Subject ('sub') missing in payload.")
            return None
        # Optionally check 'exp' claim, though jwt.decode usually does this
        return subject
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during token verification: {e}")
        return None