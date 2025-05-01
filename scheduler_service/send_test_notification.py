import argparse
import asyncio
import aio_pika
import json

async def send_notification(user_id, notif_type, title, body, link=None):
    rabbitmq_url = "amqp://guest:guest@localhost:5672/"
    exchange_name = "notification_exchange"
    routing_key = "notification.key"

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

    print("✅ Notification sent.")
    await connection.close()

def main():
    parser = argparse.ArgumentParser(description="Send a test notification via RabbitMQ")
    parser.add_argument("--user", type=int, required=True, help="User ID")
    parser.add_argument("--type", type=str, required=True, help="Notification type (e.g., promotion, order)")
    parser.add_argument("--title", type=str, required=True, help="Notification title")
    parser.add_argument("--body", type=str, required=True, help="Notification body")
    parser.add_argument("--link", type=str, help="Optional link")

    args = parser.parse_args()

    asyncio.run(send_notification(
        user_id=args.user,
        notif_type=args.type,
        title=args.title,
        body=args.body,
        link=args.link
    ))

if __name__ == "__main__":
    main()
