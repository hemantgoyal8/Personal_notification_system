import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import logging

# Load .env file from the notification_service directory
dotenv_path_notification = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path_notification, override=True)

# Configure logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    MONGO_URL: str     
    MONGO_DB_NAME: str   
    RABBITMQ_URL: str
    NOTIFICATION_EVENTS_EXCHANGE: str
    NOTIFICATION_QUEUE: str
    BINDING_KEY: str = '#' 
    LOG_LEVEL: str = "INFO"
    RABBITMQ_CONSUMER_PREFETCH_COUNT: int = 10
    RABBITMQ_CONNECT_TIMEOUT: int = 30
    NOTIFICATION_EXCHANGE_TYPE: str = "FANOUT"

    model_config = SettingsConfigDict(
        env_file=dotenv_path_notification,
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'
    )

settings = Settings()