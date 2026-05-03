"""
@module Config
@description Centralised application configuration.
             All API keys and environment variables loaded here.
             Never hardcode keys anywhere else in the codebase.
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
    RATE_LIMIT_PER_MINUTE: int = 60
    CACHE_DEFAULT_TTL: int = 300
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    APP_VERSION: str = "2.0.0"
    APP_NAME: str = "CivicPulse"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
