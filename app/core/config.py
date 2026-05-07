from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration loaded from environment variables / .env file.

    Uses pydantic-settings to read from the environment with multiple alias
    options for each field. This provides compatibility with both our own
    naming convention and Spring Boot's convention (since the original Java
    project used SPRING_DATASOURCE_* variables).
    """

    app_name: str = "managementApp Python API"
    api_prefix: str = "/api"

    # --- Database ---
    # Direct URL takes precedence (supports both DATABASE_URL and Spring alias)
    database_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL", "SPRING_DATASOURCE_URL"),
    )

    use_postgres: bool = Field(default=False, validation_alias=AliasChoices("USE_POSTGRES"))
    db_driver: str = "postgresql+psycopg"
    db_host: str = Field(default="localhost", validation_alias=AliasChoices("DB_HOST", "POSTGRES_HOST"))
    db_port: int = Field(default=5432, validation_alias=AliasChoices("DB_PORT", "POSTGRES_PORT"))
    db_name: str = Field(default="spring", validation_alias=AliasChoices("DB_NAME", "POSTGRES_DB"))
    db_user: str = Field(
        default="root",
        validation_alias=AliasChoices("DB_USER", "POSTGRES_USER", "SPRING_DATASOURCE_USERNAME"),
    )
    db_password: str = Field(
        default="password",
        validation_alias=AliasChoices("DB_PASSWORD", "POSTGRES_PASSWORD", "SPRING_DATASOURCE_PASSWORD"),
    )
    db_echo: bool = Field(default=False, validation_alias=AliasChoices("DB_ECHO"))

    # --- Task state scheduler ---
    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = 60
    task_created_to_running_minutes: int = 2
    task_running_to_done_minutes: int = 8

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sqlalchemy_database_url(self) -> str:
        """
        Build the final database URL.
        Priority: direct DATABASE_URL > PostgreSQL component variables > SQLite fallback.
        """
        if self.database_url:
            return self.database_url

        if self.use_postgres:
            encoded_password = quote_plus(self.db_password)
            return (
                f"{self.db_driver}://{self.db_user}:{encoded_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )

        return "sqlite:///./management.db"


@lru_cache
def get_settings() -> Settings:
    """
    Singleton factory for Settings.
    @lru_cache ensures the .env file is read only once per process lifetime.
    """
    return Settings()
