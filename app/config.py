from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    kafka_bootstrap_servers: str = ""
    kafka_topic: str = "url_clicks"
    base_url: str = "http://localhost:8000"
    rate_limit_per_minute: int = 100
    enable_kafka: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
