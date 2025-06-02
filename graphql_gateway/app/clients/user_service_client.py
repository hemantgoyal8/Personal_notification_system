import logging
from typing import Optional, Dict, Any
import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = settings.USER_SERVICE_BASE_URL

# Helper to build auth headers
def _get_auth_headers(token: Optional[str] = None) -> Dict[str, str]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

async def register_user(http_client: httpx.AsyncClient, name: str, email: str, password: str) -> Optional[Dict[str, Any]]:
    endpoint = "/api/v1/users/" 
    payload = {"name": name, "email": email, "password": password}
    #async with httpx.AsyncClient(timeout=10.0) as client:
    try:
        response = await http_client.post(endpoint, json=payload)
        response.raise_for_status() # Raise exception for 4xx/5xx
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"User Service Error (Register): {e.response.status_code} - {e.response.text}")
            # Propagate specific error details if possible
        error_detail = e.response.json().get("detail", "Registration failed")
        raise Exception(f"Registration failed: {error_detail}") # Raise exception for resolver
    except httpx.RequestError as e:
        logger.error(f"User Service Request Error (Register): {e}")
        raise Exception("Could not connect to User Service")
    except Exception as e:
        logger.error(f"Unexpected Error (Register): {e}", exc_info=True)
        raise Exception("An unexpected error occurred during registration")


async def login_user( 
    http_client: httpx.AsyncClient, 
    email: str, 
    password: str
) -> Optional[Dict[str, Any]]: 
    
    endpoint = "/api/v1/auth/login" # Define the endpoint path
    data = {"username": email, "password": password}
    
    logger.info(f"Client: Attempting login for {email} to endpoint {http_client.base_url}{endpoint}")

    try:
        # Use the 'endpoint' variable you defined
        response = await http_client.post(endpoint, data=data) # CHANGED 'url' to 'endpoint'
        
        response.raise_for_status() 
        logger.info(f"Client: Login successful for {email}, token received.")
        # Ensure this dictionary matches what AuthResponseType expects, e.g., {"access_token": ..., "token_type": ...}
        return response.json() 
    except httpx.HTTPStatusError as e:
        error_detail = f"Login failed at user service ({e.response.status_code})"
        try:
            # Try to get more specific error from user_service response
            error_detail = e.response.json().get("detail", error_detail)
        except Exception: 
            pass # Keep generic if response not JSON or no detail
        logger.error(f"User Service Error (Login): {e.response.status_code} - {error_detail} - Response: {e.response.text}")
        raise Exception(f"Login failed: {error_detail}")
    except httpx.RequestError as e:
        logger.error(f"User Service Request Error (Login): {e}")
        raise Exception("Could not connect to User Service for login")
    except Exception as e:
        logger.error(f"Unexpected Error (Login): {e}", exc_info=True)
        raise Exception("An unexpected error occurred during login")


async def get_current_user_me(http_client: httpx.AsyncClient, token: str) -> Optional[Dict[str, Any]]:
    """Calls the User Service to get the current user's details."""
    endpoint = "/api/v1/users/me"
    headers = {"Authorization": f"Bearer {token}"}

    if http_client:
        logger.info(f"Client (get_me): http_client.base_url = '{http_client.base_url}', requesting endpoint = '{endpoint}'")
    else:
        logger.error("Client (get_me): http_client is None!")
        raise Exception("HTTP client not available for get_me")

    try:
        response = await http_client.get(endpoint, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"User Service Error (GetUserMe): {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 401:
            raise Exception("Authentication invalid or expired")
        raise Exception("Failed to fetch user details")
    except httpx.RequestError as e:
        logger.error(f"User Service Request Error (GetUserMe): {e}")
        raise Exception("Could not connect to User Service")
    except Exception as e:
        logger.error(f"Unexpected Error (GetUserMe): {e}", exc_info=True)
        raise Exception("An unexpected error occurred fetching user details")

async def update_current_user_me(token: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Calls the User Service to update the current user's details."""
    url = f"{BASE_URL}/users/me"
    headers = _get_auth_headers(token)
    if not headers: raise Exception("Authentication token required")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.put(url, json=update_data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"User Service Error (UpdateUserMe): {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 401:
                raise Exception("Authentication invalid or expired")
            error_detail = e.response.json().get("detail", "Update failed")
            raise Exception(f"Failed to update user details: {error_detail}")
        except httpx.RequestError as e:
            logger.error(f"User Service Request Error (UpdateUserMe): {e}")
            raise Exception("Could not connect to User Service")
        except Exception as e:
            logger.error(f"Unexpected Error (UpdateUserMe): {e}", exc_info=True)
            raise Exception("An unexpected error occurred updating user details")