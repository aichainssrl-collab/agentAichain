from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Database
    database_url: str = Field(default="postgresql+asyncpg://user:password@localhost:5432/agent_aichain")
    database_echo: bool = Field(default=False)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    # Security
    secret_key: str = Field(default="test-secret-key-for-development-only")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    # AGNO
    agno_api_key: str = Field(default="test-agno-key-for-development-only")
    agno_base_url: str = Field(default="https://api.agno.io")

    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="neo4jpassword")

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000"])


settings = Settings()