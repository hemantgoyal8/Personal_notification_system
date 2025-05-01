import os
from pydantic import BaseSettings
from dotenv import load_dotenv
import logging

# Load .env file from the notification_service directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Configure logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    MONGO_DETAILS: str = os.getenv("MONGO_DETAILS", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "notification_db")
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

    NOTIFICATION_EVENTS_EXCHANGE: str = os.getenv("NOTIFICATION_EVENTS_EXCHANGE", "notification_events")
    NOTIFICATION_QUEUE: str = os.getenv("NOTIFICATION_QUEUE", "notification_service_queue")
    # Binding key could be specific if using topic exchange, '#' matches all for fanout/direct
    # Let's assume a fanout or direct exchange for simplicity, so queue name might act as binding key or '#'
    BINDING_KEY: str = '#' # Example: Use '#' for fanout or routing key for direct/topic

    class Config:
        case_sensitive = True

settings = Settings()