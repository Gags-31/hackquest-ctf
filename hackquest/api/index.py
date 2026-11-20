"""Vercel serverless entrypoint for HackQuest CTF 2026.

The whole application - API plus the built React SPA - is served through this
single ASGI handler. Mangum adapts FastAPI to Vercel's lambda-style runtime.
"""
import os
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_BACKEND = _ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Vercel's filesystem is read-only apart from /tmp, so the default database
# lives there. Set DATABASE_URL in the Vercel dashboard to use Postgres instead
# (and add psycopg2-binary to requirements.txt).
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/hackquest.db")
os.environ.setdefault("ENVIRONMENT", "production")

from app.db import init_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402

# Mangum runs with lifespan disabled, so FastAPI's startup event does not fire.
# Initialise the schema and seed the rounds/challenges here instead; both are
# idempotent and also refresh hint text on an existing database.
init_db()
from app.seed import run as seed_run  # noqa: E402,E402

seed_run()

from mangum import Mangum  # noqa: E402

handler = Mangum(fastapi_app, lifespan="off")
