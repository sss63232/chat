from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "chatgpt-fastapi"
    mongo_uri: str = "mongodb://localhost:27017/?replicaSet=rs0"
    mongo_database: str = "chatgpt"
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "chatgpt"
    # Set to "auto" for Cloudflare R2; leave empty for local MinIO.
    minio_region: str | None = None
    llm_base_url: str = "https://opencode.ai/zen/v1"
    llm_model: str = "kimi-k2.7-code"
    llm_api_key: str = ""
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
