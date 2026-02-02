from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_name: str = "AI Recruiter Assistant API"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Static files (legacy)
    static_dir: str = "/app/static"
    ssl_cert_file: str = "/app/certs/cert.pem"
    ssl_key_file: str = "/app/certs/key.pem"

    # JWT Authentication
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND_HEX_32"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # OpenRouter API
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-3.5-haiku"
    openrouter_model_fast: str = "google/gemini-2.0-flash-001"  # For resume parsing
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # OpenAI API (for embeddings)
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Redis
    redis_url: str = "redis://redis:6379/0"
    session_expire_seconds: int = 3600  # 1 hour

    # Celery
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # PostgreSQL Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/ai_recruiter"

    # File uploads
    max_upload_size_mb: int = 10
    allowed_file_extensions: list[str] = [".txt", ".docx", ".pdf"]

    @property
    def static_path(self) -> Path:
        return Path(self.static_dir)

    @property
    def static_dir_exists(self) -> bool:
        return self.static_path.exists()

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


settings = Settings()
