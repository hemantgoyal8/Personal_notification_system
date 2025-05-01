import asyncio
from notification_service.app.events.consumer import start_consumer_background

if __name__ == "__main__":
    asyncio.run(start_consumer_background())
