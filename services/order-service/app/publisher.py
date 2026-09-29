import json
import logging

import pika

from .config import settings

logger = logging.getLogger("order-service")


def publish_order_created(order: dict) -> bool:
    """Publish an order.created message. Returns False if publishing failed."""
    try:
        params = pika.URLParameters(settings.rabbitmq_url)
        params.socket_timeout = 3
        params.connection_attempts = 1

        # One short-lived connection per publish. Simple and thread-safe for a testbed.
        connection = pika.BlockingConnection(params)
        try:
            channel = connection.channel()
            channel.queue_declare(queue=settings.order_created_queue, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=settings.order_created_queue,
                body=json.dumps(order),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,  # persistent
                ),
            )
        finally:
            connection.close()
        return True
    except Exception:
        logger.exception("failed to publish order.created")
        return False