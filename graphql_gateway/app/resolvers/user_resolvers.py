import strawberry
from strawberry.exceptions import GraphQLError
import logging
from typing import Optional, Dict, Any

from ..schemas_gql.types import UserType, UserUpdateInput, UserPreferencesType
from ..clients import user_service_client
from strawberry.types import Info
from ..auth.context import GraphQLContext

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

async def resolve_get_me(info: Info) -> Optional[UserType]: # Renamed context to actual_context for clarity
    """
    Resolver for the 'me' query. Fetches the current authenticated user's details.
    """
    actual_context: GraphQLContext = info.context # Get your custom context
    
    if not actual_context.token or not actual_context.user_id: # Check if token/user_id is in context
        logger.warning("resolve_get_me: Authentication token or user_id missing from context.")
        raise GraphQLError("Authentication required. Please login.")

    logger.info(f"resolve_get_me: Fetching details for user_id '{actual_context.user_id}' using token.")
    
    try:
    
        http_service_client_instance = await actual_context.user_client 

        # Call the client function, passing the http_client and the token
        user_data_dict: Optional[Dict[str, Any]] = await user_service_client.get_current_user_me(
            http_client=http_service_client_instance, # Pass the actual client instance
            token=actual_context.token 
        )
        
        if not user_data_dict:
            logger.warning(f"resolve_get_me: No user data returned from user service for user_id '{actual_context.user_id}'.")
          
            return None
        
        preferences_dict_from_service = user_data_dict.get("preferences")
        user_preferences_obj = None
        if isinstance(preferences_dict_from_service, dict):
            try:
                # Assuming UserPreferencesType can be initialized from this dict
                user_preferences_obj = UserPreferencesType(**preferences_dict_from_service)
            except Exception as e_prefs:
                logger.error(f"resolve_get_me: Error creating UserPreferencesType from {preferences_dict_from_service}: {e_prefs}")

        return UserType(
            id=str(user_data_dict.get("id")), # Ensure ID is a string
            email=user_data_dict.get("email"),
            name=user_data_dict.get("name"),
            preferences=user_preferences_obj
        )

    except GraphQLError: # Re-raise GraphQLErrors directly
        raise
    except Exception as e:
        logger.error(f"resolve_get_me: Error fetching 'me' for user_id '{actual_context.user_id}': {e}", exc_info=True)
        raise GraphQLError(message=str(e))

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