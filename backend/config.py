"""
config.py — Application settings loaded from environment variables.

All secrets are read from .env (never committed).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Government of India Open Data API
    data_gov_api_key: str = ""
    data_gov_base_url: str = (
        "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    )

    # Google GenAI / Gemma 4
    gemini_api_key: str = ""
    gemma_model: str = "gemma-4-26b-a4b-it"

    # Transport cost assumption
    transport_rate_per_quintal_km: float = 0.6  # ₹ per quintal per km

    # Search
    default_search_radius_km: float = 150.0

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000


# Singleton — import this everywhere
settings = Settings()
