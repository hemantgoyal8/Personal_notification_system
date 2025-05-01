import strawberry
import logging
from typing import Optional

from graphql_gateway.app.schemas_gql.types import UserType, UserUpdateInput, UserPreferencesType, UserPreferencesInput
from graphql_gateway.app.clients import user_service_client
from strawberry.types import Info

logger = logging.getLogger(__name__)

# Helper to convert Pydantic UNSET to None or keep value for dict creation
def _clean_input_data(input_obj):
    if input_obj is None: return None
    data = {}
    for field, value in input_obj.__dict__.items():
        if value != strawberry.UNSET:
             # Handle nested input objects recursively
             if hasattr(value, '__dict__'):
                 nested_data = _clean_input_data(value)
                 if nested_data: # Only add if nested object had actual values
                     data[field] = nested_data
             else:
                data[field] = value
    return data if data else None # Return None if no fields were set

async def resolve_get_me(info: strawberry.types.Info) -> UserType:
    """Resolver to get the current authenticated user."""
    context = info.context
    if not context.user_id or not context.token:
        logger.warning("Attempted to access 'me' without authentication.")
        raise Exception("Authentication required")

    logger.info(f"Fetching 'me' for user: {context.user_id}")
    user_data = await user_service_client.get_current_user_me(token=context.token)
    
    prefs_data = user_data.get("preferences")
    preferences = UserPreferencesType(**prefs_data) if prefs_data else None

    return UserType(
        id=user_data.get("id", user_data.get("_id")),
        email=user_data.get("email"),
        name=user_data.get("name"),
        preferences=preferences
    )


async def resolve_update_user(info: Info, user_in: UserUpdateInput) -> UserType:
    """Resolver to update the current authenticated user."""
    context = info.context
    if not context.user_id or not context.token:
        logger.warning("Attempted to 'updateUser' without authentication.")
        raise Exception("Authentication required")

    logger.info(f"Attempting update for user: {context.user_id}")
    
    update_data = _clean_input_data(user_in)
    
    if not update_data:
         logger.info(f"Update called for user {context.user_id} with no fields to update.")
         # Optionally, return current user data immediately
         return await resolve_get_me(info)
         # raise Exception("No fields provided for update.")


    logger.debug(f"Update data for user {context.user_id}: {update_data}")

    # Client raises exceptions on failure
    updated_user_data = await user_service_client.update_current_user_me(
        token=context.token, update_data=update_data
    )

    prefs_data = updated_user_data.get("preferences")
    preferences = UserPreferencesType(**prefs_data) if prefs_data else None

    return UserType(
        id=updated_user_data.get("id", updated_user_data.get("_id")),
        email=updated_user_data.get("email"),
        name=updated_user_data.get("name"),
        preferences=preferences
    )