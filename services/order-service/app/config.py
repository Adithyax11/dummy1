from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    # Local defaults. Inside docker compose these become service names (Phase 7).
    database_url: str = "postgresql+psycopg2://testbed:testbed@localhost:5433/testbed"
    inventory_url: str = "http://localhost:8001"
    payment_url: str = "http://localhost:8002"
    http_timeout_s: float = 5.0
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/%2F"
    order_created_queue: str = "order.created"
    gateway_url: str = "http://localhost:8000"


settings = Settings()