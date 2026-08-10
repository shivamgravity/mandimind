"""
config.py — Application settings loaded from environment variables.

Supports three secret sources (in priority order):
  1. Real environment variables (set by the OS / docker)
  2. .env file (local development)
  3. Streamlit st.secrets (Streamlit Cloud deployment)
"""

import os
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


def _apply_streamlit_secrets(s: Settings) -> Settings:
    """
    If running on Streamlit Cloud, pull missing keys from st.secrets.
    This is a no-op when Streamlit is not installed or secrets are not set.
    """
    try:
        import streamlit as st  # noqa: PLC0415
        secrets = st.secrets  # raises if not in a Streamlit context
        if not s.data_gov_api_key:
            s.data_gov_api_key = secrets.get("DATA_GOV_API_KEY", "")
        if not s.gemini_api_key:
            s.gemini_api_key = secrets.get("GEMINI_API_KEY", "")
        if not s.gemma_model or s.gemma_model == "gemma-4-26b-a4b-it":
            s.gemma_model = secrets.get("GEMMA_MODEL", s.gemma_model)
    except Exception:
        pass  # Not running in Streamlit — skip silently
    return s


# Singleton — import this everywhere
settings = _apply_streamlit_secrets(Settings())
