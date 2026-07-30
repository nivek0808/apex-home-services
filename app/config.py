"""Application configuration loaded from environment variables."""

from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    # Local LLM
    LOCAL_LLM_URL: str = os.getenv("LOCAL_LLM_URL", "http://localhost:8080/v1")

    # Invoice Ninja
    INVOICE_NINJA_URL: str = os.getenv("INVOICE_NINJA_URL", "http://localhost:8003")
    INVOICE_NINJA_TOKEN: str = os.getenv("INVOICE_NINJA_TOKEN", "your_ninja_api_token")

    # Cal.com
    CALCOM_API_URL: str = os.getenv("CALCOM_API_URL", "http://localhost:3000/api/v1")

    # Webhooks
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    VAPI_API_KEY: str = os.getenv("VAPI_API_KEY", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///apex_sandbox.db")

    # App
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"


settings = Settings()