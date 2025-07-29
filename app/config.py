"""
Application configuration using pydantic-settings.
"""
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application
    app_name: str = "LLM Template System"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = Field(default="development", pattern="^(development|testing|production)$")
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "llm_template_system"
    
    # OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    
    # LLM Providers
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ollama_base_url: str = "http://localhost:11434"
    
    # Celery
    celery_broker_url: str = ""
    celery_result_backend: str = ""
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("celery_broker_url", mode="before")
    @classmethod
    def set_celery_broker(cls, v, values):
        if not v and values.data.get("mongodb_url"):
            return f"{values.data['mongodb_url']}/{values.data.get('mongodb_db_name', 'llm_template_system')}"
        return v
    
    @field_validator("celery_result_backend", mode="before")
    @classmethod
    def set_celery_backend(cls, v, values):
        if not v and values.data.get("mongodb_url"):
            return f"{values.data['mongodb_url']}/{values.data.get('mongodb_db_name', 'llm_template_system')}"
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()