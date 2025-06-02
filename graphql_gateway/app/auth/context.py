# graphql_gateway/app/auth/context.py
from typing import Optional
from strawberry.fastapi import BaseContext
from httpx import AsyncClient
from starlette.requests import Request # For type hinting

from .security import verify_token # Assuming verify_token is in auth/security.py
from ..core.config import settings, logger # Import settings and logger

class GraphQLContext(BaseContext):
    user_id: Optional[str]
    token: Optional[str]
    _user_client: Optional[AsyncClient] = None
    _notification_client: Optional[AsyncClient] = None

    async def _initialize_clients(self): # This is an internal helper method
        if self._user_client is None:
            logger.info(f"Context: Initializing user_client with base_url from settings: '{settings.USER_SERVICE_BASE_URL}'") # Use UPPERCASE_WITH_BASE
            self._user_client = AsyncClient(base_url=settings.USER_SERVICE_BASE_URL, timeout=10.0) # Use UPPERCASE_WITH_BASE
        if self._notification_client is None:
            logger.info(f"Context: Initializing notification_client with base_url from settings: '{settings.NOTIFICATION_SERVICE_BASE_URL}'") # Use UPPERCASE_WITH_BASE
            self._notification_client = AsyncClient(base_url=settings.NOTIFICATION_SERVICE_BASE_URL, timeout=10.0) # Use UPPERCASE_WITH_BASE

    @property
    async def user_client(self) -> AsyncClient:
        await self._initialize_clients()
        return self._user_client

    @property
    async def notification_client(self) -> AsyncClient:
        await self._initialize_clients()
        return self._notification_client

    def __init__(
        self,
        request: Request,
        user_id: Optional[str],
        token: Optional[str],
    ):
        super().__init__() # Call parent init
        self.request = request 
        self.user_id = user_id
        self.token = token

async def get_context(request: Request) -> GraphQLContext:
    token: Optional[str] = None
    user_id: Optional[str] = None
    auth_header = request.headers.get("Authorization", None)

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1]
        try:
            payload = verify_token(token) # verify_token should return payload or raise error
            user_id = payload.get("sub") if payload else None # Assuming 'sub' contains user_id/email
            if not user_id:
                logger.warning(f"Token payload does not contain user_id (sub): {payload}")
                token = None # Invalidate token if no user_id
        except Exception as e: # Catch JWTError, ExpiredSignatureError etc. from verify_token
            logger.warning(f"Invalid token received for request {request.url.path}: {e}")
            token = None
            user_id = None
            
    return GraphQLContext(
        request=request,
        user_id=user_id,
        token=token,
    )