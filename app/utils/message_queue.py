import os
import json
import pika
import ssl
from dotenv import load_dotenv
from app.state.connections import ws_connections
from app.loggers.custom import logger
from app.sql.user_crud import create_user
from app.routes.socket_routes import send_response

load_dotenv()
rabbitmq_host = os.getenv("RABBITMQ_HOST")
rabbitmq_port = int(os.getenv("RABBITMQ_PORT"))
rabbitmq_username = os.getenv("RABBITMQ_USERNAME")
rabbitmq_password = os.getenv("RABBITMQ_PASSWORD")

ssl_context = ssl.create_default_context()
ssl_options = pika.SSLOptions(context=ssl_context, server_hostname=rabbitmq_host)

credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
params = pika.ConnectionParameters(
    host=rabbitmq_host,
    port=rabbitmq_port,
    credentials=credentials,
    ssl_options=ssl_options,
)
connection = pika.BlockingConnection(params)
channel = connection.channel()


channel.exchange_declare(exchange="websocket_exchange", exchange_type="fanout")
result = channel.queue_declare(queue="", exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange="websocket_exchange", queue=queue_name)


def rabbitmq_message_publisher(from_number, contact_name):
    message_data = {"from_number": from_number, "contact_name": contact_name}
    channel.basic_publish(
        exchange="websocket_exchange", routing_key="", body=json.dumps(message_data)
    )
    logger.info("Published to websocket_exchange")


def rabbitmq_message_handler(ch, method, properties, body):
    data = json.loads(body)
    from_number = data["from_number"]
    contact_name = data["contact_name"]

    if from_number in ws_connections:
        ws = ws_connections.pop(from_number)
        send_response(
            ws, "Confirm", f"Thank you for confirming your number, {contact_name}!"
        )
        ws.close()
        logger.info("Dispatched response via WebSocket and closed connection")
        create_user(from_number, contact_name)
    else:
        logger.info(f"No WebSocket connection found for {from_number}")


def subscribe_to_rabbitmq_channel():
    channel.basic_consume(
        queue=queue_name, on_message_callback=rabbitmq_message_handler, auto_ack=True
    )
    logger.info("Subscribed to RabbitMQ channel")
    channel.start_consuming()
