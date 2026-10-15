"""Organizer administration: rounds, competition state, proctoring, audit, exports."""
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..audit import record, recent
from ..config import settings
from ..db import get_db
from ..deps import (current_actor, require_admin, require_organizer,
                    scoring_mode, setting)
from ..models import (AuditLog, Challenge, Organizer, Round, RoundState,
                      ScoringMode, Submission, Team, TeamStatus, Violation)
from ..scoring import (csv_report, leaderboard, max_possible, scoring_summary)
from ..security import hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])


class RoundUpdate(BaseModel):
    number: int
    state: str | None = None
    explanation: str | None = None


class SettingUpdate(BaseModel):
    key: str = Field(max_length=60)
    value: str = Field(max_length=400)


class ReviewAction(BaseModel):
    violation_id: int
    forgive: bool = True
    reason: str = Field(min_length=3, max_length=255)


class DqAction(BaseModel):
    team_id: int
    reason: str = Field(min_length=3, max_length=255)
    restore: bool = False


class OrgCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: str
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=12, max_length=200)
    role: str = "moderator"


# ------------------------------------------------------------------ rounds
@router.post("/rounds")
def update_round(payload: RoundUpdate, request: Request, response: Response,
                 db: Session = Depends(get_db)):
    actor = require_organizer(request, db)
    rd = db.query(Round).filter_by(number=payload.number).first()
    if not rd:
        raise HTTPException(404, "Round not found.")
    if payload.state:
        try:
            rd.state = RoundState(payload.state)
        except ValueError:
            raise HTTPException(422, "state must be locked, open or closed.")
    if payload.explanation is not None:
        rd.explanation = payload.explanation
    db.commit()
    record(db, actor=actor.name, action="round.updated",
           target=f"round{payload.number}",
           detail=f"state={rd.state.value}", request=request)
    return {"ok": True, "number": rd.number, "state": rd.state.value}


@router.post("/competition")
def competition_state(state: str, request: Request, response: Response,
                      db: Session = Depends(get_db)):
    actor = require_admin(request, db)
    if state not in ("pending", "running", "paused", "ended"):
        raise HTTPException(422, "Invalid competition state.")
    from ..models import AppSetting
    row = db.query(AppSetting).filter_by(key="competition_state").first()
    if not row:
        row = AppSetting(key="competition_state", value=state)
        db.add(row)
    else:
        row.value = state
    db.commit()
    record(db, actor=actor.name, action="competition.state", target=state, request=request)
    return {"ok": True, "state": state}


# ------------------------------------------------------------------ settings
@router.get("/settings")
def read_settings(request: Request, db: Session = Depends(get_db)):
    require_organizer(request, db)
    from ..models import AppSetting
    rows = db.query(AppSetting).all()
    return {"settings": {r.key: r.value for r in rows},
            "scoring": scoring_summary(scoring_mode(db)),
            "limits": {
                "proctor_violations": settings.PROCTOR_VIOLATION_LIMIT,
                "hint_penalty_default": settings.HINT_PENALTY,
            },
            "email_configured": settings.email_configured}


ALLOWED_SETTINGS = {
    "scoring_mode", "hint_penalty", "registration_open", "competition_state",
    "event_datetime", "event_timezone", "results_frozen", "results_published",
    "max_participants_note",
}


@router.post("/settings")
def update_setting(payload: SettingUpdate, request: Request, response: Response,
                   db: Session = Depends(get_db)):
    actor = require_admin(request, db)
    if payload.key not in ALLOWED_SETTINGS:
        raise HTTPException(422, f"'{payload.key}' is not a configurable setting.")
    if payload.key == "scoring_mode" and payload.value not in (ScoringMode.TIER.value,
                                                              ScoringMode.NORMALIZED.value):
        raise HTTPException(422, "scoring_mode must be 'tier' or 'normalized'.")
    from ..models import AppSetting
    row = db.query(AppSetting).filter_by(key=payload.key).first()
    if not row:
        row = AppSetting(key=payload.key, value="")
        db.add(row)
    old = row.value
    row.value = payload.value
    db.commit()
    record(db, actor=actor.name, action="setting.updated", target=payload.key,
           detail=f"{old!r} -> {payload.value!r}", request=request)
    return {"ok": True, "key": payload.key, "value": payload.value}


# ------------------------------------------------------------------ teams
@router.get("/teams")
def list_teams(request: Request, db: Session = Depends(get_db)):
    require_organizer(request, db)
    teams = db.query(Team).order_by(Team.id).all()
    mode = scoring_mode(db)
    from ..scoring import team_stats
    out = []
    for t in teams:
        out.append({"id": t.id, "name": t.name, "code": t.team_code,
                    "leader_email": t.leader_email, "status": t.status.value,
                    "email_verified": t.email_verified,
                    "members": [{"name": m.name, "email": m.email,
                                 "is_leader": m.is_leader} for m in t.members],
                    **team_stats(db, t, mode, 0)})
    return {"teams": out}


@router.post("/teams/verify")
def verify_team(team_id: int, request: Request, response: Response,
                db: Session = Depends(get_db)):
    actor = require_organizer(request, db)
    t = db.get(Team, team_id)
    if not t:
        raise HTTPException(404, "Team not found.")
    t.status = TeamStatus.VERIFIED
    t.email_verified = True
    db.commit()
    record(db, actor=actor.name, action="team.verified", target=t.team_code,
           request=request)
    return {"ok": True, "team": t.name, "status": t.status.value}


# ------------------------------------------------------------------ proctoring
@router.get("/violations")
def list_violations(request: Request, db: Session = Depends(get_db)):
    require_organizer(request, db)
    rows = db.query(Violation).order_by(Violation.at.desc()).limit(500).all()
    return {"limit": settings.PROCTOR_VIOLATION_LIMIT,
            "violations": [{
                "id": v.id, "team": v.team.name if v.team else "?",
                "kind": v.kind, "at": v.at.isoformat() if v.at else None,
                "reviewed": v.reviewed, "forgiven": v.forgiven,
                "review_note": v.review_note, "reviewed_by": v.reviewed_by,
            } for v in rows]}


@router.post("/violations/review")
def review_violation(payload: ReviewAction, request: Request, response: Response,
                     db: Session = Depends(get_db)):
    actor = require_organizer(request, db)
    v = db.get(Violation, payload.violation_id)
    if not v:
        raise HTTPException(404, "Violation not found.")
    if v.reviewed:
        raise HTTPException(409, "This violation has already been reviewed.")
    v.reviewed = True
    v.forgiven = payload.forgive
    v.review_note = payload.reason
    v.reviewed_by = actor.name
    db.commit()
    record(db, actor=actor.name,
           action="violation.forgiven" if payload.forgive else "violation.upheld",
           target=f"violation:{v.id}", detail=payload.reason, request=request)
    return {"ok": True, "violation_id": v.id, "forgiven": v.forgiven}


@router.post("/teams/disqualify")
def disqualify(payload: DqAction, request: Request, response: Response,
               db: Session = Depends(get_db)):
    actor = require_admin(request, db)
    t = db.get(Team, payload.team_id)
    if not t:
        raise HTTPException(404, "Team not found.")
    t.status = TeamStatus.ACTIVE if payload.restore else TeamStatus.DISQUALIFIED
    db.commit()
    record(db, actor=actor.name,
           action="team.restored" if payload.restore else "team.disqualified",
           target=t.team_code, detail=payload.reason, request=request)
    return {"ok": True, "team": t.name, "status": t.status.value}


# ------------------------------------------------------------------ organizers
@router.get("/organizers")
def list_organizers(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    rows = db.query(Organizer).all()
    return {"organizers": [{"id": o.id, "username": o.username, "email": o.email,
                            "full_name": o.full_name, "role": o.role,
                            "must_change_password": o.must_change_password,
                            "last_login_at": o.last_login_at.isoformat()
                            if o.last_login_at else None} for o in rows]}


@router.post("/organizers", status_code=201)
def create_organizer(payload: OrgCreate, request: Request, response: Response,
                     db: Session = Depends(get_db)):
    require_admin(request, db)
    if db.query(Organizer).filter_by(username=payload.username).first():
        raise HTTPException(409, "Username already exists.")
    org = Organizer(username=payload.username, email=payload.email,
                    full_name=payload.full_name, role=payload.role,
                    password_hash=hash_password(payload.password),
                    must_change_password=True)
    db.add(org)
    db.commit()
    record(db, actor=request.cookies.get("x") or "admin",
           action="organizer.created", target=org.username, request=request)
    return {"ok": True, "username": org.username, "role": org.role}


# ------------------------------------------------------------------ reports
@router.get("/leaderboard")
def admin_board(request: Request, db: Session = Depends(get_db)):
    require_organizer(request, db)
    mode = scoring_mode(db)
    from ..deps import hint_penalty
    rows = leaderboard(db, mode, hint_penalty(db))
    return {"rows": rows, "scoring": scoring_summary(mode),
            "max_possible": max_possible(mode)}


@router.get("/export/leaderboard.csv")
def export_leaderboard(request: Request, db: Session = Depends(get_db)):
    require_organizer(request, db)
    mode = scoring_mode(db)
    from ..deps import hint_penalty
    rows = leaderboard(db, mode, hint_penalty(db))
    return Response(csv_report(rows), media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=hackquest-leaderboard.csv"})


@router.get("/export/registrations.csv")
def export_registrations(request: Request, db: Session = Depends(get_db)):
    require_organizer(request, db)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Team", "Code", "Leader", "Leader email", "College", "Branch",
                "Semester", "Members", "Status", "Verified"])
    for t in db.query(Team).all():
        members = "; ".join(m.name for m in t.members)
        w.writerow([t.name, t.team_code, t.leader_name, t.leader_email, t.college,
                    t.branch, t.semester, members, t.status.value, t.email_verified])
    return Response(buf.getvalue(), media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=hackquest-registrations.csv"})


@router.get("/export/submissions.csv")
def export_submissions(request: Request, db: Session = Depends(get_db)):
    require_organizer(request, db)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Team", "Round", "Challenge", "Correct", "Points", "Attempts",
                "Hints", "Submitted"])
    rows = db.execute(select(Submission).order_by(Submission.at)).scalars().all()
    for s in rows:
        w.writerow([s.team.name, s.round_number, s.challenge_key, s.correct,
                    s.points_awarded, s.attempt_number, s.hint_used,
                    s.at.isoformat() if s.at else ""])
    return Response(buf.getvalue(), media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=hackquest-submissions.csv"})


# ------------------------------------------------------------------ audit
@router.get("/audit")
def audit_trail(request: Request, limit: int = 200, db: Session = Depends(get_db)):
    require_organizer(request, db)
    rows = recent(db, min(limit, 1000))
    return {"entries": [{"id": r.id, "actor": r.actor, "action": r.action,
                         "target": r.target, "detail": r.detail,
                         "at": r.at.isoformat() if r.at else None,
                         "ip": r.ip} for r in rows]}


# ------------------------------------------------------------------ submissions view
@router.get("/submissions")
def list_submissions(request: Request, team_id: int | None = None,
                     db: Session = Depends(get_db)):
    require_organizer(request, db)
    q = select(Submission).order_by(Submission.at.desc())
    if team_id:
        q = q.where(Submission.team_id == team_id)
    rows = db.execute(q.limit(1000)).scalars().all()
    return {"submissions": [{
        "team": s.team.name if s.team else "?", "round": s.round_number,
        "challenge": s.challenge_key, "correct": s.correct,
        "points": s.points_awarded, "attempts": s.attempt_number,
        "hints": s.hint_used,
        "at": s.at.isoformat() if s.at else None} for s in rows]}


# ------------------------------------------------------------------ unlock progress
@router.get("/unlocks")
def unlock_progress(request: Request, db: Session = Depends(get_db)):
    require_organizer(request, db)
    from ..models import RoundUnlock
    rows = db.query(RoundUnlock).all()
    return {"unlocks": [{"team": r.team.name if r.team else "?",
                         "round": r.round_number,
                         "at": r.unlocked_at.isoformat() if r.unlocked_at else None}
                        for r in rows]}