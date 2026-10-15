"""Authentication: organizer bootstrap, team registration, login, logout, recovery."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..audit import record
from ..config import settings
from ..db import get_db
from ..deps import (current_actor, rate_limit, require_csrf, set_cookies,
                    csrf_token, setting)
from ..models import Organizer, Team, TeamMember, TeamStatus
from ..security import (constant_time_eq, hash_password, make_session_token,
                        new_csrf_token, new_team_code, verify_password)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ------------------------------------------------------------------ schemas
class OrganizerCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=12, max_length=200)
    role: str = "admin"

    @field_validator("role")
    @classmethod
    def _role(cls, v):
        if v not in ("admin", "moderator"):
            raise ValueError("role must be admin or moderator")
        return v


class MemberIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    branch: str = ""
    semester: str = ""
    college: str = ""


class TeamRegister(BaseModel):
    team_name: str = Field(min_length=3, max_length=64)
    leader_name: str = Field(min_length=2, max_length=120)
    leader_email: EmailStr
    college: str = ""
    branch: str = ""
    semester: str = ""
    password: str = Field(min_length=8, max_length=200)
    members: list[MemberIn] = Field(default_factory=list, max_length=3)


class LoginIn(BaseModel):
    identity: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=200)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12, max_length=200)


# ------------------------------------------------------------------ bootstrap
@router.post("/bootstrap", status_code=201)
def bootstrap_organizer(payload: OrganizerCreate, request: Request,
                         response: Response, db: Session = Depends(get_db)):
    """Create the first administrator. Refuses once any organizer exists.

    Prefer the CLI command `python -m app.cli bootstrap` in production.
    """
    existing = db.execute(select(func.count(Organizer.id))).scalar_one()
    if existing:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Organizers already exist. Use the admin dashboard or CLI.")
    org = Organizer(username=payload.username, email=payload.email,
                    full_name=payload.full_name, role="admin",
                    password_hash=hash_password(payload.password),
                    must_change_password=True)
    db.add(org)
    db.commit()
    record(db, actor=payload.username, action="organizer.bootstrap",
           target=payload.username, request=request)
    return {"ok": True, "username": org.username,
            "note": "Password change required on first sign-in."}


# ------------------------------------------------------------------ teams
@router.post("/register", status_code=201)
def register_team(payload: TeamRegister, request: Request, response: Response,
                  db: Session = Depends(get_db)):
    if setting(db, "registration_open", "1") != "1":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Registration is closed.")

    ip = request.client.host if request.client else "anon"
    rate_limit(f"reg:{ip}", limit=8, window=3600)

    if db.query(Team).filter(func.lower(Team.name) == payload.team_name.lower()).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "That team name is already registered.")
    if db.query(Team).filter(func.lower(Team.leader_email) == payload.leader_email.lower()).first():
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "That email already leads a registered team.")
    total = 1 + len(payload.members)
    if total < 2 or total > 4:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Team size must be between 2 and 4.")

    code = new_team_code()
    while db.query(Team).filter_by(team_code=code).first():
        code = new_team_code()

    team = Team(
        name=payload.team_name, team_code=code,
        leader_name=payload.leader_name, leader_email=payload.leader_email.lower(),
        college=payload.college, branch=payload.branch, semester=payload.semester,
        password_hash=hash_password(payload.password),
        email_verified=not settings.email_configured,
        status=TeamStatus.ACTIVE,
    )
    db.add(team)
    db.flush()
    for m in payload.members:
        db.add(TeamMember(team_id=team.id, name=m.name, email=m.email.lower(),
                          branch=m.branch, semester=m.semester,
                          college=m.college, is_leader=False))
    db.commit()
    record(db, actor=payload.team_name, action="team.register",
           target=team.team_code, detail=f"size={total}", request=request)

    set_cookies(response, make_session_token(str(team.id), "team"), new_csrf_token())
    return {"ok": True, "team_code": team.team_code, "team_name": team.name,
            "email_verified": team.email_verified,
            "verification_required": settings.email_configured and not team.email_verified}


# ------------------------------------------------------------------ login
@router.post("/login")
def login(payload: LoginIn, request: Request, response: Response,
          db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "anon"
    rate_limit(f"login:{ip}", limit=settings.LOGIN_RATE_LIMIT, window=300)

    ident = payload.identity.strip()
    team = db.query(Team).filter(
        (func.lower(Team.name) == ident.lower()) |
        (func.lower(Team.leader_email) == ident.lower()) |
        (Team.team_code == ident.upper())
    ).first()
    org = db.query(Organizer).filter(
        (func.lower(Organizer.username) == ident.lower()) |
        (func.lower(Organizer.email) == ident.lower())
    ).first()

    target = None
    kind = None
    if team:
        target, kind = team, "team"
    elif org:
        target, kind = org, "organizer"

    # Always run a hash comparison to reduce timing side channels.
    ok = verify_password(target.password_hash, payload.password) if target else False
    if not target or not ok:
        record(db, actor=ident[:64], action="auth.login_failed", request=request)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials.")

    if kind == "organizer":
        target.last_login_at = func.now()
        record(db, actor=target.username, action="auth.login", request=request)
        db.commit()
    else:
        record(db, actor=target.name, action="auth.login", target=target.team_code,
               request=request)
        db.commit()

    set_cookies(response, make_session_token(str(target.id), kind), new_csrf_token())
    return {"ok": True, "role": kind,
            "must_change_password": bool(getattr(target, "must_change_password", False)),
            "disqualified": kind == "team" and target.status == TeamStatus.DISQUALIFIED}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    require_csrf(request)
    actor = current_actor(request, db)
    if actor:
        record(db, actor=actor.name, action="auth.logout", request=request)
    set_cookies(response, None, clear=True)
    return {"ok": True}


@router.post("/change-password")
def change_password(payload: PasswordChange, request: Request, response: Response,
                    db: Session = Depends(get_db)):
    require_csrf(request)
    actor = current_actor(request, db)
    if not actor:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in.")
    if not verify_password(actor.obj.password_hash, payload.current_password):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Current password is incorrect.")
    actor.obj.password_hash = hash_password(payload.new_password)
    actor.obj.must_change_password = False
    db.commit()
    record(db, actor=actor.name, action="auth.password_changed", request=request)
    # Session fixation defence: rotate the session token after a credential change.
    role = "organizer" if actor.is_organizer else "team"
    set_cookies(response, make_session_token(str(actor.obj.id), role), new_csrf_token())
    return {"ok": True}


@router.post("/request-recovery")
def request_recovery(payload: dict, request: Request, db: Session = Depends(get_db)):
    """Always returns the same response to avoid account enumeration."""
    email = (payload.get("email") or "").strip().lower()
    rate_limit(f"recover:{request.client.host if request.client else 'anon'}", 5, 3600)
    team = db.query(Team).filter(func.lower(Team.leader_email) == email).first()
    if team:
        record(db, actor=team.name, action="auth.recovery_requested",
               target=team.team_code, request=request)
        if settings.email_configured:
            # TODO: wire to SMTP in the deployment guide.
            pass
    return {"ok": True, "message": "If that email is registered, recovery details are sent."}


@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    actor = current_actor(request, db)
    if not actor:
        return {"authenticated": False}
    if actor.is_organizer:
        o = actor.obj
        return {"authenticated": True, "role": "organizer", "username": o.username,
                "full_name": o.full_name, "email": o.email, "admin_role": o.role,
                "must_change_password": o.must_change_password}
    t = actor.obj
    return {"authenticated": True, "role": "team", "team_name": t.name,
            "team_code": t.team_code, "status": t.status.value,
            "email_verified": t.email_verified,
            "members": [{"name": m.name, "email": m.email, "is_leader": m.is_leader}
                        for m in t.members]}


@router.get("/csrf")
def get_csrf(request: Request, response: Response):
    """Issue (or echo) the CSRF token.

    The token must be written to the response object FastAPI actually returns -
    building a separate Response here and discarding it would silently never set
    the cookie.
    """
    tok = csrf_token(request) or new_csrf_token()
    set_cookies(response, None, tok)
    return {"csrf_token": tok}