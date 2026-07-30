"""Application configuration with environment variable support."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env from project root (parent of app/)
_project_root = Path(__file__).resolve().parent.parent
dotenv_path = _project_root / ".env"
load_dotenv(dotenv_path)


class Settings:
    """Application settings loaded from environment variables."""

    # App settings
    APP_NAME: str = "Apex Home Services"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Google AI Studio API (primary LLM)
    # Primary models based on free tier limits
    GOOGLE_AI_API_KEY: str = os.getenv("GOOGLE_AI_API_KEY", "")
    GOOGLE_AI_MODEL_PRIMARY: str = os.getenv("GOOGLE_AI_MODEL_PRIMARY", "gemini-3.5-flash-lite")
    GOOGLE_AI_MODEL_FALLBACK: str = os.getenv("GOOGLE_AI_MODEL_FALLBACK", "gemma-4-31b-it")
    GOOGLE_AI_COOLDOWN_SECONDS: int = int(os.getenv("GOOGLE_AI_COOLDOWN_SECONDS", "60"))
    GOOGLE_AI_TEMPERATURE: float = float(os.getenv("GOOGLE_AI_TEMPERATURE", "0.3"))
    GOOGLE_AI_MAX_TOKENS: int = int(os.getenv("GOOGLE_AI_MAX_TOKENS", "4096"))

    # Legacy local LLM (for backwards compatibility)
    LOCAL_LLM_URL: str = os.getenv("LOCAL_LLM_URL", "http://localhost:8080/v1")

    # Invoice Ninja
    INVOICE_NINJA_TOKEN: str = os.getenv("INVOICE_NINJA_TOKEN", "")
    INVOICE_NINJA_URL: str = os.getenv("INVOICE_NINJA_URL", "http://localhost:8003")

    # Cal.com
    CALCOM_API_URL: str = os.getenv("CALCOM_API_URL", "http://localhost:3000/api/v1")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./apex_sandbox.db")

    @property
    def google_ai_available(self) -> bool:
        """Check if Google AI API key is configured."""
        return bool(self.GOOGLE_AI_API_KEY.strip())

    @property
    def llm_provider(self) -> str:
        """Return the active LLM provider."""
        return "google_ai" if self.google_ai_available else "local_fallback"


settings = Settings()