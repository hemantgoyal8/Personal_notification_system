import os
from pydantic import BaseSettings
from dotenv import load_dotenv
import logging

# Load .env file from the graphql_gateway directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level_str, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    USER_SERVICE_BASE_URL: str = os.getenv("USER_SERVICE_BASE_URL", "http://localhost:8000/api/v1")
    NOTIFICATION_SERVICE_BASE_URL: str = os.getenv("NOTIFICATION_SERVICE_BASE_URL", "http://localhost:8001/api/v1")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "default_secret") # Must match User Service
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256") # Must match User Service

    class Config:
        case_sensitive = True

settings = Settings()