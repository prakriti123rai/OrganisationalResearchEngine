from functools import lru_cache
from typing import Optional

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
    neo4j_auth: str = "neo4j/orepassword"
    reasoning_model: str = "gpt-5.5"
    openai_api_key: Optional[str] = None
    openai_responses_url: str = "https://api.openai.com/v1/responses"
    openai_timeout_seconds: int = 45

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def neo4j_uri(self) -> str:
        return f"bolt://{self.neo4j_host}:{self.neo4j_bolt_port}"

    @property
    def neo4j_user(self) -> str:
        return self.neo4j_auth.split("/", 1)[0]

    @property
    def neo4j_password(self) -> str:
        parts = self.neo4j_auth.split("/", 1)
        return parts[1] if len(parts) == 2 else ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
