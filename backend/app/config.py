from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Organizational Reasoning Engine"
    app_version: str = "0.1.0"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "ore"
    postgres_password: str = "ore"
    postgres_db: str = "ore"
    neo4j_host: str = "localhost"
    neo4j_bolt_port: int = 7687
    neo4j_http_port: int = 7474

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
