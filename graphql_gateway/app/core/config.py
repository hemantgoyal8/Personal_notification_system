import os
from pydantic_settings import BaseSettings
from pydantic import SettingsConfigDict
from dotenv import load_dotenv
import logging

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level_str, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    USER_SERVICE_BASE_URL: str 
    NOTIFICATION_SERVICE_BASE_URL: str
    JWT_SECRET_KEY: str 
    JWT_ALGORITHM: str = "HS256"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=dotenv_path, 
        case_sensitive=True, 
        extra='ignore'
    )

settings = Settings()
logger.info(f"GraphQL Gateway - USER_SERVICE_BASE_URL: {settings.USER_SERVICE_BASE_URL}") # Add this log!
logger.info(f"GraphQL Gateway - NOTIFICATION_SERVICE_BASE_URL: {settings.NOTIFICATION_SERVICE_BASE_URL}") # Add this log!
