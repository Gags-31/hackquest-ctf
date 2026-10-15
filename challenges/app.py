"""HackQuest CTF 2026 - Render entrypoint.

The live platform is the FastAPI application in ../hackquest/backend.
This shim exists so the existing Render service keeps working with its
configured start command:

    gunicorn app:app        (from the `challenges/` directory)

gunicorn serves the ASGI app directly, and the FastAPI app serves the built
React SPA from hackquest/frontend/dist.

Implementation note
-------------------
This file is itself named `app`, which would shadow the backend's `app`
package if we simply added it to sys.path. So the backend is imported under
the alias `hq_backend` using importlib, leaving sys.modules["app"] pointing
at this shim where gunicorn expects to find it.
"""
import importlib
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(_HERE), "hackquest", "backend"))
_PKG = os.path.join(_BACKEND, "app")

# Deployment-safe defaults so the service boots without dashboard changes.
# Replace SECRET_KEY with a real random value in the host environment.
os.environ.setdefault(
    "SECRET_KEY",
    os.environ.get("SECRET_KEY", "hackquest-render-dev-secret-change-me"),
)
os.environ.setdefault("ENVIRONMENT", os.environ.get("ENVIRONMENT", "production"))
os.environ.setdefault(
    "DATABASE_URL", os.environ.get("DATABASE_URL", "sqlite:///./hackquest.db")
)

if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

_spec = importlib.util.spec_from_file_location(
    "hq_backend",
    os.path.join(_PKG, "__init__.py"),
    submodule_search_locations=[_PKG],
)
_pkg = importlib.util.module_from_spec(_spec)
sys.modules["hq_backend"] = _pkg
_spec.loader.exec_module(_pkg)

app = importlib.import_module("hq_backend.main").app  # noqa: E402

if __name__ == "__main__":  # pragma: no cover - local development only
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))