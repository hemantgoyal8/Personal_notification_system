import asyncio
import aio_pika
import json

async def send_notification(user_id: int, notif_type: str, title: str, body: str, link: str = None):
    rabbitmq_url = "amqp://guest:guest@localhost/"
    exchange_name = "notification_exchange"
    routing_key = "notification.key"  # ignored if ExchangeType.FANOUT

    message_body = {
        "userId": user_id,
        "type": notif_type,
        "content": {
            "title": title,
            "body": body,
            "link": link
        }
    }

    connection = await aio_pika.connect_robust(rabbitmq_url)
    channel = await connection.channel()

    exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.FANOUT, durable=True)

    await exchange.publish(
        aio_pika.Message(body=json.dumps(message_body).encode()),
        routing_key=routing_key
    )

    print(f"✅ Notification sent to user {user_id}")
    await connection.close()
