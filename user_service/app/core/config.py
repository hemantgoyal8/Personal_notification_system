import os
from pydantic import BaseSettings
from dotenv import load_dotenv

# Load .env file from the user_service directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class Settings(BaseSettings):
    MONGO_DETAILS: str = os.getenv("MONGO_DETAILS", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "user_db")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "default_secret") # Fallback, but .env is preferred
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # Optional RabbitMQ settings if needed later
    # RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    # USER_EVENTS_EXCHANGE: str = os.getenv("USER_EVENTS_EXCHANGE", "user_events")

    class Config:
        case_sensitive = True
        # If not using docker/env variables directly, load from .env file
        # env_file = '.env' # This can sometimes conflict with manual load_dotenv

settings = Settings()