"""Configuration for Imprint Chat API."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str
    supabase_url: str
    supabase_anon_key: str

    # LLM APIs
    openai_api_key: str
    anthropic_api_key: str

    # LangSmith
    langsmith_api_key: str | None = None
    langsmith_tracing: bool = False
    langsmith_project: str = "imprint-chatbot"

    # CORS - can be set via CORS_ORIGINS env var as comma-separated list
    cors_origins: str = "http://localhost:3000,https://imprint-ruddy.vercel.app"

    class Config:
        env_file = "../.env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
