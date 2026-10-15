"""HackQuest CTF 2026 - configuration.

All secrets come from the environment. .env.example contains placeholders only.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _b(key: str, default: bytes) -> bytes:
    v = os.getenv(key)
    return v.encode() if v else default


class Settings:
    APP_NAME = "HackQuest CTF 2026"
    ORG_NAME = "Pragyan x IEEE-CS KLEIT Chapter"
    TAGLINE = "Break the Target. Own the Flag."

    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "0") == "1"

    # Use PostgreSQL in production; SQLite for local development.
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR/'hackquest.db'}")

    # MUST be overridden in production with a long random value.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-insecure-change-me")
    SESSION_COOKIE = "hq_session"
    SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE", str(60 * 60 * 12)))
    CSRF_COOKIE = "hq_csrf"

    # Argon2id
    ARGON2_TIME_COST = int(os.getenv("ARGON2_TIME_COST", "3"))
    ARGON2_MEMORY_COST = int(os.getenv("ARGON2_MEMORY_COST", "65536"))
    ARGON2_PARALLELISM = int(os.getenv("ARGON2_PARALLELISM", "4"))

    # Two independent organizer accounts, created by the bootstrap command.
    ADMIN_BOOTSTRAP_USER = os.getenv("ADMIN_BOOTSTRAP_USER", "")
    ADMIN_BOOTSTRAP_EMAIL = os.getenv("ADMIN_BOOTSTRAP_EMAIL", "")

    # Competition
    PROCTOR_VIOLATION_LIMIT = int(os.getenv("PROCTOR_VIOLATION_LIMIT", "3"))
    HINT_PENALTY = int(os.getenv("HINT_PENALTY", "0"))
    SUBMIT_RATE_LIMIT = int(os.getenv("SUBMIT_RATE_LIMIT", "30"))
    LOGIN_RATE_LIMIT = int(os.getenv("LOGIN_RATE_LIMIT", "10"))
    HINT_RATE_LIMIT = int(os.getenv("HINT_RATE_LIMIT", "20"))

    # Email verification is optional and only active when SMTP is configured.
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "")

    ALLOWED_ORIGINS = [o for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o]

    @property
    def email_configured(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)

    @property
    def using_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


settings = Settings()