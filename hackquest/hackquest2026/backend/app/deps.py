"""Request dependencies: sessions, CSRF, rate limiting and actor resolution."""
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import HTTPException, Request

from .config import FLAG_RATE_LIMIT
from .db import get_db
from .models import Organizer, Team, TeamStatus
from .security import new_csrf_token, read_session

_counters: dict = defaultdict(deque)


@dataclass
class Actor:
    kind: str
    obj: object

    @property
    def is_team(self) -> bool:
        return self.kind == "team"

    @property
    def is_org(self) -> bool:
        return self.kind == "organizer"

    @property
    def id(self) -> int:
        return self.obj.id


def current_actor(request: Request, db) -> Actor | None:
    token = request.cookies.get("hq_session")
    if not token:
        return None
    data = read_session(token)
    if not data:
        return None
    if data.get("t") == "organizer":
        obj = db.get(Organizer, int(data["i"]))
        return Actor("organizer", obj) if obj else None
    if data.get("t") == "team":
        obj = db.get(Team, int(data["i"]))
        if obj and obj.status == TeamStatus.APPROVED:
            return Actor("team", obj)
    return None


def require_team(request: Request, db) -> Actor:
    actor = current_actor(request, db)
    if not actor or not actor.is_team:
        raise HTTPException(401, "Team login required")
    return actor


def require_org(request: Request, db) -> Actor:
    actor = current_actor(request, db)
    if not actor or not actor.is_org:
        raise HTTPException(403, "Organiser access required")
    return actor


def ensure_csrf(request: Request) -> None:
    header = request.headers.get("x-csrf-token", "")
    cookie = request.cookies.get("hq_csrf", "")
    if not header or not cookie or header != cookie:
        raise HTTPException(403, "CSRF token missing or invalid")


def set_auth_cookies(response, token: str, secure: bool = False) -> None:
    response.set_cookie(
        "hq_session", token, httponly=True, samesite="lax",
        secure=secure, max_age=12 * 3600, path="/",
    )


def rate_limit(key: str, limit: int = FLAG_RATE_LIMIT, window: int = 60) -> None:
    now = time.time()
    q = _counters[key]
    while q and q[0] < now - window:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(429, "Too many attempts. Please slow down.")
    q.append(now)


def csrf_pair(response) -> str:
    token = new_csrf_token()
    response.set_cookie("hq_csrf", token, samesite="lax", httponly=False, path="/")
    return token
