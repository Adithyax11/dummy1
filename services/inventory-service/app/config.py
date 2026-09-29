from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Host port is 5433 when running locally. Inside docker compose it will be postgres:5432.
    database_url: str = "postgresql+psycopg2://testbed:testbed@localhost:5433/testbed"


settings = Settings()