import asyncio
from scheduler_service.app.events.producer import RabbitMQProducer  # Assuming you have this class
import random

fake_titles = [
    "Recommended: New Laptops",
    "Based on your shopping: Headphones",
    "Flash Sale: Gaming Chairs",
    "Exclusive: Smartwatches Under ₹999"
]

fake_bodies = [
    "Get your favorite tech products now!",
    "Trending picks just for you.",
    "Don't miss out on this limited-time deal.",
    "Your style, your price — shop now."
]

async def generate_recommendation_notifications():
    producer = RabbitMQProducer()
    await producer.connect()

    for user_id in range(1, 4):  # Simulate for 3 users
        title = random.choice(fake_titles)
        body = random.choice(fake_bodies)

        payload = {
            "userId": user_id,
            "type": "recommendation",
            "content": {
                "title": title,
                "body": body,
                "link": "https://example.com/recommendations"
            }
        }

        await producer.send_message(payload)
        print(f"✅ Sent recommendation to user {user_id}")

    await producer.close()
