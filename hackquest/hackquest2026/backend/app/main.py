"""HACKQUEST CTF 2026 — FastAPI application entry point."""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .routers import admin, auth, public, team
from .seed import run as seed_run

app = FastAPI(title="HACKQUEST CTF 2026", version="1.0.0",
              docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public.router)
app.include_router(auth.router)
app.include_router(team.router)
app.include_router(admin.router)

_SEEDED = False


def ensure_seeded():
    global _SEEDED
    if _SEEDED:
        return
    try:
        init_db()
        seed_run(refresh=True)
        _SEEDED = True
    except Exception as exc:  # keep health endpoint alive on read-only FS
        if "readonly" not in str(exc).lower() and "read-only" not in str(exc).lower():
            raise


@app.on_event("startup")
def on_startup():
    ensure_seeded()


@app.middleware("http")
async def seed_once(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        ensure_seeded()
    return await call_next(request)


@app.get("/api/health")
def api_health():
    return {"status": "ok", "event": "HACKQUEST CTF 2026"}


FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if FRONTEND_DIST.exists():
    assets = FRONTEND_DIST / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
def spa(full_path: str):
    if full_path.startswith("api/"):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"detail": "Frontend build not found"}, status_code=503)
