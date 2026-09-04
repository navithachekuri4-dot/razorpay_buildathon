"""
Central configuration for the AI Revenue Recovery Agent.

Everything that changes between a laptop demo, a CI test run, and a real
deployment lives here and is read from environment variables. Nothing in
this file is a secret — actual secrets come from .env (not committed).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./revenue_recovery.db")

    # --- Gemini ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
    GEMINI_TIMEOUT_SECONDS: float = 8.0

    # --- Razorpay Test Mode ---
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "").strip()
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "").strip()

    # --- Agent safety configuration (deterministic, not AI-tunable) ---
    MAX_RETRY_COUNT: int = int(os.getenv("MAX_RETRY_COUNT", "3"))

    # Allowed recovery actions. Any AI output outside this set is rejected
    # and treated as an invalid response (safe fallback kicks in).
    ALLOWED_ACTIONS = {
        "retry_now",
        "retry_after_delay",
        "send_update_card_link",
        "escalate",
        "stop_no_retry",
        "verify_then_decide",
    }


settings = Settings()
