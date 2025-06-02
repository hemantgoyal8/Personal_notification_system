import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv 
import logging

# Load .env file from the scheduler_service directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)

log_level_env = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    RABBITMQ_URL: str 
    ORDER_EVENTS_EXCHANGE: str
    PROMOTION_EVENTS_EXCHANGE: str 
    RECOMMENDATION_EVENTS_EXCHANGE: str = "recommendation_events_exchange"
    USER_SERVICE_URL: str = "http://user_service:8001" 
    NOTIFICATION_EVENTS_EXCHANGE: str = "notification_events"
    # Exchange type should match what Notification Service expects (e.g., FANOUT)
    NOTIFICATION_EXCHANGE_TYPE: str = "fanout"

    ORDER_UPDATE_JOB_INTERVAL_SECONDS: int = 60
    PROMOTION_JOB_INTERVAL_SECONDS: int =  180

    LOG_LEVEL: str = "INFO" 

    model_config = SettingsConfigDict(
        env_file=dotenv_path,
        env_file_encoding='utf-8',
        case_sensitive=True, 
        extra='ignore'
    )
    
settings = Settings()

logging.getLogger().setLevel(settings.LOG_LEVEL.upper())
logger.setLevel(settings.LOG_LEVEL.upper())


logger.info(f"Scheduler Service Settings Loaded:")
logger.info(f"  RABBITMQ_URL: {settings.RABBITMQ_URL}")
logger.info(f"  USER_SERVICE_URL: {settings.USER_SERVICE_URL}")
logger.info(f"  ORDER_EVENTS_EXCHANGE: {settings.ORDER_EVENTS_EXCHANGE}")
logger.info(f"  PROMOTION_EVENTS_EXCHANGE: {settings.PROMOTION_EVENTS_EXCHANGE}")
logger.info(f"  RECOMMENDATION_EVENTS_EXCHANGE: {settings.RECOMMENDATION_EVENTS_EXCHANGE}")
logger.info(f"  NOTIFICATION_EVENTS_EXCHANGE: {settings.NOTIFICATION_EVENTS_EXCHANGE}")
logger.info(f"  NOTIFICATION_EXCHANGE_TYPE: {settings.NOTIFICATION_EXCHANGE_TYPE}")
logger.info(f"  ORDER_UPDATE_JOB_INTERVAL_SECONDS: {settings.ORDER_UPDATE_JOB_INTERVAL_SECONDS}")
logger.info(f"  PROMOTION_JOB_INTERVAL_SECONDS: {settings.PROMOTION_JOB_INTERVAL_SECONDS}")
logger.info(f"  LOG_LEVEL: {settings.LOG_LEVEL}")