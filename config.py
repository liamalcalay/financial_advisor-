"""Environment-backed application settings."""

import os

from dotenv import load_dotenv

load_dotenv()


def get_app_mode() -> str:
    """Return the supported operating mode for the Streamlit dashboard."""

    mode = os.getenv("APP_MODE", "local").strip().lower()
    if mode not in {"local", "demo"}:
        return "local"

    return mode
