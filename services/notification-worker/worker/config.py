from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/%2F"
    order_created_queue: str = "order.created"
    min_send_ms: int = 100     # simulated time to "send" a notification
    max_send_ms: int = 400


settings = Settings()