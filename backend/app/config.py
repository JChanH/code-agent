"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file or environment."""

    # App
    app_name: str = "Code Agent"
    debug: bool = Field(default=False, validation_alias=AliasChoices("DEBUG_MODE", "DEBUG"))

    # Database
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "code_agent"
    
    # redis
    redis_secrete_key: str = ""
    redis_base_url: str = "localhost"
    redis_base_port: int = 6379
    redis_database: int = 0

    # Anthropic
    anthropic_api_key: str = ""
    max_concurrent_tasks: int = Field(default=2, validation_alias="MAX_CONCURRENT_TASKS")

    @property
    def redis_url(self) -> str:
        return (
            f"redis://:{self.redis_secrete_key}@{self.redis_base_url}"
            f":{self.redis_base_port}/{self.redis_database}"
        )

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def async_database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_prefix="",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
