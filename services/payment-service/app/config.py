from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    failure_rate: float = 0.1      # env: FAILURE_RATE (0.0 to 1.0)
    min_latency_ms: int = 50       # env: MIN_LATENCY_MS
    max_latency_ms: int = 500      # env: MAX_LATENCY_MS


settings = Settings()