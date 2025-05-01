import strawberry
import logging
from typing import Optional

from graphql_gateway.app.schemas_gql.types import UserRegisterInput, UserType, AuthResponseType, UserPreferencesType
from graphql_gateway.app.clients import user_service_client
from graphql_gateway.app.auth.context import GraphQLContext # Use the type hint

logger = logging.getLogger(__name__)

async def resolve_register_user(user_in: UserRegisterInput) -> UserType:
    """Resolver for user registration."""
    logger.info(f"Attempting registration for email: {user_in.email}")
    # Client function now raises exceptions on failure
    user_data = await user_service_client.register_user(
        name=user_in.name, email=user_in.email, password=user_in.password
    )
    # If client didn't raise, assume success and map data
    # Preferences might be nested, handle potential None
    prefs_data = user_data.get("preferences")
    preferences = UserPreferencesType(**prefs_data) if prefs_data else None
    
    return UserType(
        id=user_data.get("id", user_data.get("_id")), # Use id or _id from response
        email=user_data.get("email"),
        name=user_data.get("name"),
        preferences=preferences
    )


async def resolve_login(email: str, password: str) -> AuthResponseType:
    """Resolver for user login."""
    logger.info(f"Attempting login for email: {email}")
    # Client function raises exceptions on failure
    auth_data = await user_service_client.login_user(email=email, password=password)
    return AuthResponseType(
        access_token=auth_data.get("access_token"),
        token_type=auth_data.get("token_type", "bearer")
    )