"""Environment-driven configuration for HACKQUEST CTF 2026."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


SECRET_KEY = _env("SECRET_KEY", "dev-only-change-me-hackquest-2026")
DATABASE_URL = _env("DATABASE_URL", f"sqlite:///{BASE_DIR / 'backend' / 'hackquest2026.db'}")
ENVIRONMENT = _env("ENVIRONMENT", "development")
SESSION_HOURS = int(_env("SESSION_HOURS", "12"))
FLAG_RATE_LIMIT = int(_env("FLAG_RATE_LIMIT", "12"))  # attempts per 60s per team
ORG1_PASSWORD = _env("ORG1_PASSWORD", "")
ORG2_PASSWORD = _env("ORG2_PASSWORD", "")
ORG1_USERNAME = _env("ORG1_USERNAME", "pragyan_lead")
ORG2_USERNAME = _env("ORG2_USERNAME", "ieee_lead")

IS_PRODUCTION = ENVIRONMENT.lower() == "production"
