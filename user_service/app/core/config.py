import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import logging

dotenv_path_user = os.path.join(os.path.dirname(__file__), '..', '..', '.env') # Points to user_service/.env
load_dotenv(dotenv_path=dotenv_path_user, override=True)

class Settings(BaseSettings):
    MONGO_URL: str 
    RABBITMQ_URL: str 
    MONGO_DB_NAME: str 
    JWT_SECRET_KEY: str 
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    LOG_LEVEL: str = "INFO" 

    model_config = SettingsConfigDict(
        env_file=dotenv_path_user,
        case_sensitive=True,
        extra='ignore'
    )

settings = Settings()

log_level_to_use = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(level=log_level_to_use, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info(f"User Service Settings Loaded:")
logger.info(f"  DATABASE_URL: {'********'}") # Don't log full DB URL with password
logger.info(f"  RABBITMQ_URL: {settings.RABBITMQ_URL}")
logger.info(f"  JWT_SECRET: {'********'}")
logger.info(f"  JWT_ALGORITHM: {settings.JWT_ALGORITHM}")
logger.info(f"  ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
logger.info(f"  LOG_LEVEL: {settings.LOG_LEVEL}")