"""Vercel serverless entry point for HACKQUEST CTF 2026."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.main import app as _app  # noqa: E402


class _PathNormalizer:
    """Some Vercel router configs prepend the function path; strip it safely."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            path = scope.get("path", "")
            for prefix in ("/api/index.py", "/api/index"):
                if path == prefix:
                    scope = dict(scope)
                    scope["path"] = "/"
                    break
                if path.startswith(prefix + "/"):
                    scope = dict(scope)
                    scope["path"] = path[len(prefix):]
                    break
        await self.inner(scope, receive, send)


app = _PathNormalizer(_app)

__all__ = ["app", "handler"]

handler = app
