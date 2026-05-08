from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    redis_url: str
    kafka_bootstrap_servers: str = ""
    kafka_topic: str = "url_clicks"
    base_url: str = "http://localhost:8000"
    rate_limit_per_minute: int = 100
    enable_kafka: bool = False


settings = Settings()
