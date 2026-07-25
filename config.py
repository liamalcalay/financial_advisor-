"""Environment-backed application settings."""

import os

from dotenv import load_dotenv

load_dotenv()


def get_app_mode(configured_mode: str | None = None) -> str:
    """Return the supported operating mode for the Streamlit dashboard."""

    mode = (configured_mode or os.getenv("APP_MODE", "local")).strip().lower()
    if mode not in {"local", "demo"}:
        return "local"

    return mode
