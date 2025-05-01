# graphql_gateway/app/auth/context.py

from typing import Optional, Dict
import strawberry
from fastapi import Request, Depends
from strawberry.fastapi import BaseContext
from httpx import AsyncClient

from .security import verify_token
from graphql_gateway.app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Context(BaseContext):
    """Custom context class for Strawberry requests."""
    user_id: Optional[str] = None
    token: Optional[str] = None
    user_client: Optional[AsyncClient] = None
    notification_client: Optional[AsyncClient] = None
    request: Optional[Request] = None

async def get_context(request: Request) -> Context:
    """
    FastAPI dependency to create the GraphQL context.
    Verifies JWT and initializes HTTP clients.
    """
    token: Optional[str] = None
    user_id: Optional[str] = None
    auth_header = request.headers.get("Authorization", None)

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1]
        user_id = verify_token(token)
        if not user_id:
            logger.warning(f"Invalid token received for request {request.url.path}")
            token = None

    # Create httpx clients within the request scope
    async with AsyncClient(base_url=settings.USER_SERVICE_BASE_URL, timeout=10.0) as user_client, \
               AsyncClient(base_url=settings.NOTIFICATION_SERVICE_BASE_URL, timeout=10.0) as notif_client:

        return Context(
            user_id=user_id,
            token=token,
            user_client=user_client,
            notification_client=notif_client,
            request=request
        )

