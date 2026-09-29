import json
import logging
import random
import time

import pika

from .config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("notification-worker")


def handle(channel, method, properties, body):
    try:
        order = json.loads(body)
    except ValueError:
        log.error("malformed message, discarding: %r", body)
        channel.basic_nack(method.delivery_tag, requeue=False)
        return

    time.sleep(random.randint(settings.min_send_ms, settings.max_send_ms) / 1000)

    log.info(
        "notification sent: order #%s confirmed (%s x%s, $%.2f)",
        order.get("id"), order.get("sku"), order.get("quantity"),
        order.get("total_cents", 0) / 100,
    )
    channel.basic_ack(method.delivery_tag)


def run():
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
            channel = connection.channel()
            channel.queue_declare(queue=settings.order_created_queue, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=settings.order_created_queue, on_message_callback=handle
            )
            log.info("waiting for messages on '%s'", settings.order_created_queue)
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            log.warning("rabbitmq unavailable, retrying in 5s")
            time.sleep(5)
        except KeyboardInterrupt:
            log.info("shutting down")
            break


if __name__ == "__main__":
    run()