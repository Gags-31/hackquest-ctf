"""FastAPI application factory for HackQuest CTF 2026."""
import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import BASE_DIR, settings
from .db import init_db
from .routers import admin, auth, public, rounds

app = FastAPI(
    title=settings.APP_NAME,
    description=f"{settings.ORG_NAME} — {settings.TAGLINE}",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
)

if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )


@app.on_event("startup")
def _startup():
    init_db()
    os.makedirs(BASE_DIR / "sandbox_workspace", exist_ok=True)
    # Self-initialising deployment: on a fresh database (e.g. a Render free
    # instance with an ephemeral disk) seed the rounds and challenges, otherwise
    # the arena would boot with nothing to play.
    from .db import SessionLocal
    from .models import Round
    con = SessionLocal()
    try:
        empty = con.query(Round).count() == 0
    finally:
        con.close()
    if empty:
        from .seed import run as seed_run
        seed_run()


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    # No inline script from third parties; the SPA is bundled locally.
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
    return response


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Never surface raw internal errors that could leak answer keys."""
    return JSONResponse(status_code=422,
                        content={"detail": "The request could not be processed."})


app.include_router(auth.router)
app.include_router(rounds.router)
app.include_router(public.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"ok": True, "app": settings.APP_NAME, "env": settings.ENVIRONMENT,
            "database": "sqlite" if settings.using_sqlite else "postgresql"}


# Serve the built SPA if present (single-container deployment).
# StaticFiles(html=True) only resolves directory requests, so client-side routes
# such as /rules or /login would 404 on a hard refresh. Mount the asset
# directory and add an explicit history fallback to index.html.
_dist = BASE_DIR.parent / "frontend" / "dist"
if _dist.is_dir():
    from fastapi.responses import FileResponse

    app.mount("/assets", StaticFiles(directory=str(_dist / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        candidate = _dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(_dist / "index.html"))