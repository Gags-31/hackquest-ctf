"""Team registration, login, logout and password management."""
import re
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..audit import record
from ..config import IS_PRODUCTION
from ..db import get_db
from ..deps import current_actor, csrf_pair, ensure_csrf, set_auth_cookies
from ..models import Organizer, Team, TeamMember, TeamStatus
from ..security import (constant_time_eq, hash_password, make_session,
                        new_csrf_token, new_team_code, verify_password)

router = APIRouter(prefix="/api/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MOBILE_RE = re.compile(r"^[0-9+\-\s()]{7,20}$")


class MemberIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(max_length=255)
    mobile: str = Field(max_length=32)


class RegisterIn(BaseModel):
    team_name: str = Field(min_length=3, max_length=120)
    college: str = Field(min_length=2, max_length=180)
    department: str = Field(min_length=2, max_length=120)
    semester: str = Field(min_length=1, max_length=40)
    leader_name: str = Field(min_length=2, max_length=120)
    leader_email: str = Field(max_length=255)
    leader_mobile: str = ""
    password: str = Field(min_length=8, max_length=200)
    members: List[MemberIn]

    @property
    def all_emails(self):
        return [self.leader_email.strip().lower()] + [m.email.strip().lower() for m in self.members]


class LoginIn(BaseModel):
    username: str = Field(min_length=2, max_length=120)
    password: str = Field(max_length=200)


class PasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=200)


@router.get("/csrf")
def get_csrf(response: Response):
    return {"csrf": csrf_pair(response)}


@router.get("/session")
def session(request: Request, db: Session = Depends(get_db)):
    actor = current_actor(request, db)
    if not actor:
        return {"role": None}
    if actor.is_org:
        return {"role": "organizer", "username": actor.obj.username,
                "must_change_password": actor.obj.must_change_password}
    return {"role": "team", "username": actor.obj.name, "team_id": actor.obj.id,
            "status": actor.obj.status.value}


@router.post("/register", status_code=201)
def register(payload: RegisterIn, response: Response, db: Session = Depends(get_db)):
    emails = payload.all_emails
    if len(emails) != len(set(emails)):
        raise HTTPException(400, "Each participant email must be unique within the team")
    for email in emails:
        if not EMAIL_RE.match(email):
            raise HTTPException(400, f"Invalid email address: {email}")
    if not (1 <= len(payload.members) <= 3):
        raise HTTPException(400, "A team must have 2 to 4 participants (leader + 1 to 3 members)")
    for m in payload.members:
        if not MOBILE_RE.match(m.mobile.strip()):
            raise HTTPException(400, "Invalid mobile number format")
    if db.scalar(select(Team.id).where(Team.name == payload.team_name.strip())):
        raise HTTPException(409, "Team name already registered")
    dup = db.scalar(
        select(TeamMember.id).where(TeamMember.email.in_(emails))
    )
    if dup:
        raise HTTPException(409, "A participant is already registered with another team")
    if db.scalar(select(Team.id).where(Team.leader_email == emails[0])):
        raise HTTPException(409, "A participant is already registered with another team")

    code = new_team_code()
    while db.scalar(select(Team.id).where(Team.code == code)):
        code = new_team_code()

    team = Team(
        name=payload.team_name.strip(), college=payload.college.strip(),
        department=payload.department.strip(), semester=payload.semester.strip(),
        leader_name=payload.leader_name.strip(), leader_email=emails[0],
        password_hash=hash_password(payload.password), code=code,
        status=TeamStatus.PENDING,
    )
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, name=payload.leader_name.strip(),
                      email=emails[0],
                      mobile=(payload.leader_mobile or payload.members[0].mobile).strip(),
                      is_leader=True))
    for m in payload.members:
        db.add(TeamMember(team_id=team.id, name=m.name.strip(),
                          email=m.email.strip().lower(), mobile=m.mobile.strip()))
    record(db, "team", team.id, "registration_submitted", team.name)
    db.commit()
    return {
        "message": "Registration submitted. Await organiser approval.",
        "team_id": team.id, "team_name": team.name, "status": "pending",
        "csrf": csrf_pair(response),
    }


@router.post("/login")
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    username = payload.username.strip()
    org = db.scalar(select(Organizer).where(Organizer.username == username))
    if org and verify_password(org.password_hash, payload.password):
        token = make_session("organizer", org.id)
        set_auth_cookies(response, token, secure=IS_PRODUCTION)
        record(db, "organizer", org.id, "login")
        db.commit()
        return {
            "role": "organizer", "username": org.username,
            "must_change_password": org.must_change_password,
            "csrf": csrf_pair(response),
        }
    team = db.scalar(select(Team).where(Team.name == username))
    if team and verify_password(team.password_hash, payload.password):
        if team.status != TeamStatus.APPROVED:
            raise HTTPException(403, "Team is not approved yet")
        token = make_session("team", team.id)
        set_auth_cookies(response, token, secure=IS_PRODUCTION)
        record(db, "team", team.id, "login")
        db.commit()
        return {
            "role": "team", "username": team.name, "team_id": team.id,
            "must_change_password": False,
            "csrf": csrf_pair(response),
        }
    raise HTTPException(401, "Invalid credentials")


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    actor = current_actor(request, db)
    if actor:
        record(db, actor.kind, actor.id, "logout")
        db.commit()
    response.delete_cookie("hq_session", path="/")
    response.delete_cookie("hq_csrf", path="/")
    return {"ok": True}


@router.post("/change-password")
def change_password(payload: PasswordIn, request: Request, db: Session = Depends(get_db)):
    actor = current_actor(request, db)
    if not actor:
        raise HTTPException(401, "Login required")
    ensure_csrf(request)
    if not verify_password(actor.obj.password_hash, payload.current_password):
        raise HTTPException(400, "Current password is incorrect")
    if constant_time_eq(payload.current_password, payload.new_password):
        raise HTTPException(400, "New password must be different")
    actor.obj.password_hash = hash_password(payload.new_password)
    actor.obj.must_change_password = False
    record(db, actor.kind, actor.id, "password_changed")
    db.commit()
    return {"ok": True}
