import strawberry
from strawberry.types import Info
from strawberry.exceptions import GraphQLError
import logging
from typing import Optional

from ..schemas_gql.types import UserRegisterInput, UserType, AuthResponseType, UserPreferencesType
from ..clients import user_service_client
from ..auth.context import GraphQLContext

logger = logging.getLogger(__name__)

async def resolve_register_user(info: Info, user_in: UserRegisterInput) -> UserType:
    actual_context: GraphQLContext = info.context
    user_service_http_client = await actual_context.user_client
    logger.info(f"Attempting registration for email: {user_in.email}")
    # Client function now raises exceptions on failure
    
    user_data = await user_service_client.register_user(
        http_client=user_service_http_client, name=user_in.name, email=user_in.email, password=user_in.password
        )
    prefs_data = user_data.get("preferences")
    preferences = UserPreferencesType(**prefs_data) if prefs_data else None
    
    return UserType(
        id=user_data.get("id", user_data.get("_id")), # Use id or _id from response
        email=user_data.get("email"),
        name=user_data.get("name"),
        preferences=preferences
    )


async def resolve_login(info: Info, email: str, password: str) -> AuthResponseType:
    logger.info(f"Attempting login for email: {email}")
    actual_context: GraphQLContext = info.context
    user_service_http_client = await actual_context.user_client 

    try:
        token_data_dict = await user_service_client.login_user(
            http_client=user_service_http_client,
            email=email,
            password=password
        )
        
        if not token_data_dict or "access_token" not in token_data_dict:
            logger.error(f"Login for {email} did not return valid token data from user service.")
            raise strawberry.GraphQLError("Login failed: Invalid response from authentication service.")

        # Map the dictionary from the client to your AuthResponseType Pydantic/Strawberry model
        return AuthResponseType(
            access_token=token_data_dict.get("access_token"),
            token_type=token_data_dict.get("token_type", "bearer")
        )
    except Exception as e:
        logger.error(f"Error during login for {email}: {e}", exc_info=True)
        raise GraphQLError(message=str(e))