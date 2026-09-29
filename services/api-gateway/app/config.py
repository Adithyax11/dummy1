from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Local defaults. Inside docker compose these become service names (Phase 7).
    order_url: str = "http://localhost:8003"
    inventory_url: str = "http://localhost:8001"
    http_timeout_s: float = 10.0


settings = Settings()