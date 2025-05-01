import os
from pydantic import BaseSettings
from dotenv import load_dotenv
import logging

# Load .env file from the scheduler_service directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Configure logging early
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    USER_SERVICE_BASE_URL: str = os.getenv("USER_SERVICE_BASE_URL", "http://localhost:8000/api/v1")

    NOTIFICATION_EVENTS_EXCHANGE: str = os.getenv("NOTIFICATION_EVENTS_EXCHANGE", "notification_events")
    # Exchange type should match what Notification Service expects (e.g., FANOUT)
    NOTIFICATION_EXCHANGE_TYPE: str = os.getenv("NOTIFICATION_EXCHANGE_TYPE", "fanout")

    ORDER_UPDATE_JOB_INTERVAL_SECONDS: int = int(os.getenv("ORDER_UPDATE_JOB_INTERVAL_SECONDS", 60))
    PROMOTION_JOB_INTERVAL_SECONDS: int = int(os.getenv("PROMOTION_JOB_INTERVAL_SECONDS", 180))

    class Config:
        case_sensitive = True

settings = Settings()