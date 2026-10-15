"""Shared dependencies: settings cache, auth, CSRF, rate limiting."""
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import AppSetting, Organizer, ScoringMode, Team, TeamStatus
from .security import csrf_ok, read_session_token


def setting(db: Session, key: str, default: str = "") -> str:
    row = db.query(AppSetting).filter_by(key=key).first()
    return row.value if row else default


def scoring_mode(db: Session) -> ScoringMode:
    raw = setting(db, "scoring_mode", ScoringMode.TIER.value)
    try:
        return ScoringMode(raw)
    except ValueError:
        return ScoringMode.TIER


def hint_penalty(db: Session) -> int:
    try:
        return int(setting(db, "hint_penalty", "0") or 0)
    except ValueError:
        return 0


# ------------------------------------------------------------------ CSRF
def set_cookies(response: Response, session_token: str | None, csrf: str | None = None,
                clear: bool = False):
    secure = settings.ENVIRONMENT == "production"
    if clear:
        response.delete_cookie(settings.SESSION_COOKIE)
        response.delete_cookie(settings.CSRF_COOKIE)
        return
    if session_token:
        response.set_cookie(
            settings.SESSION_COOKIE, session_token,
            max_age=settings.SESSION_MAX_AGE, httponly=True,
            secure=secure, samesite="lax", path="/")
    if csrf:
        # Readable by JS so the SPA can echo it in the X-CSRF-Token header.
        response.set_cookie(
            settings.CSRF_COOKIE, csrf,
            max_age=settings.SESSION_MAX_AGE, httponly=False,
            secure=secure, samesite="lax", path="/")


def csrf_token(request: Request) -> str | None:
    return request.cookies.get(settings.CSRF_COOKIE)


def require_csrf(request: Request):
    sent = request.headers.get("X-CSRF-Token")
    expected = request.cookies.get(settings.CSRF_COOKIE)
    if not csrf_ok(sent, expected):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF validation failed.")


# ------------------------------------------------------------------ rate limiting
_hits: dict[str, deque] = defaultdict(deque)


def rate_limit(key: str, limit: int, window: int = 60):
    now = time.time()
    dq = _hits[key]
    while dq and now - dq[0] > window:
        dq.popleft()
    if len(dq) >= limit:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            "Too many requests. Please slow down.")
    dq.append(now)


# ------------------------------------------------------------------ auth
class Actor:
    def __init__(self, kind, obj):
        self.kind = kind
        self.obj = obj
        self.id = obj.id
        self.name = getattr(obj, "username", None) or getattr(obj, "name", "")

    @property
    def is_organizer(self):
        return self.kind == "organizer"

    @property
    def is_team(self):
        return self.kind == "team"

    @property
    def is_admin(self):
        return self.is_organizer and self.obj.role == "admin"


def current_actor(request: Request, db: Session = Depends(get_db)) -> Actor | None:
    token = request.cookies.get(settings.SESSION_COOKIE)
    if not token:
        return None
    data = read_session_token(token)
    if not data:
        return None
    if data.get("role") == "organizer":
        org = db.get(Organizer, int(data["id"]))
        return Actor("organizer", org) if org else None
    team = db.get(Team, int(data["id"]))
    if team and team.status != TeamStatus.DISQUALIFIED:
        return Actor("team", team)
    if team:
        return Actor("team", team)   # visible but flagged as disqualified
    return None


def require_team(request: Request, db: Session = Depends(get_db)) -> Actor:
    require_csrf(request)
    actor = current_actor(request, db)
    if not actor or not actor.is_team:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in as a team.")
    return actor


def require_organizer(request: Request, db: Session = Depends(get_db)) -> Actor:
    require_csrf(request)
    actor = current_actor(request, db)
    if not actor or not actor.is_organizer:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Organizer access required.")
    return actor


def require_admin(request: Request, db: Session = Depends(get_db)) -> Actor:
    actor = require_organizer(request, db)
    if not actor.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator role required.")
    return actor