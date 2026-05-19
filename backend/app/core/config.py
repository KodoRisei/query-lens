from enum import StrEnum
from functools import lru_cache

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    development = "development"
    staging = "staging"
    production = "production"


class LLMProvider(StrEnum):
    openai = "openai"
    anthropic = "anthropic"
    ollama = "ollama"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "QueryLens"
    environment: Environment = Environment.development
    debug: bool = False
    log_level: str = "INFO"

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default=["http://localhost:3000"])

    # Database
    database_url: PostgresDsn = Field(  # type: ignore[assignment]
        default="postgresql+asyncpg://user:password@localhost:5432/querylens"
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # AI Provider
    default_llm_provider: LLMProvider = LLMProvider.ollama
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"

    # Analysis
    explain_analyze_timeout_seconds: int = 30
    max_query_length: int = 50_000

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return upper

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.production


@lru_cache
def get_settings() -> Settings:
    return Settings()
