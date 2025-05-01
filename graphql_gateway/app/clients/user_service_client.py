import logging
from typing import Optional, Dict, Any
import httpx

from graphql_gateway.app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = settings.USER_SERVICE_BASE_URL

# Helper to build auth headers
def _get_auth_headers(token: Optional[str] = None) -> Dict[str, str]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

async def register_user(name: str, email: str, password: str) -> Optional[Dict[str, Any]]:
    """Calls the User Service to register a new user."""
    url = f"{BASE_URL}/users/"
    payload = {"name": name, "email": email, "password": password}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload)
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


async def login_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Calls the User Service to log in and get a JWT."""
    url = f"{BASE_URL}/auth/login"
    # User Service expects OAuth2PasswordRequestForm (form data)
    data = {"username": email, "password": password}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, data=data, headers=headers)
            response.raise_for_status()
            return response.json() # Should return {"access_token": "...", "token_type": "bearer"}
        except httpx.HTTPStatusError as e:
            logger.error(f"User Service Error (Login): {e.response.status_code} - {e.response.text}")
            error_detail = e.response.json().get("detail", "Login failed")
            raise Exception(f"Login failed: {error_detail}")
        except httpx.RequestError as e:
            logger.error(f"User Service Request Error (Login): {e}")
            raise Exception("Could not connect to User Service")
        except Exception as e:
            logger.error(f"Unexpected Error (Login): {e}", exc_info=True)
            raise Exception("An unexpected error occurred during login")


async def get_current_user_me(token: str) -> Optional[Dict[str, Any]]:
    """Calls the User Service to get the current user's details."""
    url = f"{BASE_URL}/users/me"
    headers = _get_auth_headers(token)
    if not headers: raise Exception("Authentication token required")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers)
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