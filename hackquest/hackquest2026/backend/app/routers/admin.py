"""Organiser command centre APIs. Both organiser accounts have full access."""
from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..audit import record
from ..db import get_db
from ..deps import ensure_csrf, require_org
from ..exportutil import to_csv, to_pdf
from ..models import (Announcement, AuditLog, Challenge, Meme, Organizer,
                      Riddle, Round, RoundState, Submission, Team, TeamMember,
                      TeamStatus)
from ..seed import get_setting, set_setting
from ..security import (as_utc, hash_password, new_team_code, utcnow,
                        verify_password)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ------------------------------------------------------------------ helpers
def _actor(request: Request, db: Session):
    return require_org(request, db)


def _log(db, actor, action, detail=""):
    record(db, "organizer", actor.id, action, detail)


# ------------------------------------------------------------------ overview
@router.get("/overview")
def overview(request: Request, db: Session = Depends(get_db)):
    _actor(request, db)
    subs = db.scalars(select(Submission)).all()
    current = db.scalar(
        select(Round).where(Round.state.in_([RoundState.OPEN, RoundState.PAUSED]))
        .order_by(Round.number.desc())
    )
    return {
        "teams_total": db.scalar(select(func.count()).select_from(Team)) or 0,
        "participants": db.scalar(select(func.count()).select_from(TeamMember)) or 0,
        "pending": db.scalar(select(func.count()).select_from(Team).where(
            Team.status == TeamStatus.PENDING)) or 0,
        "approved": db.scalar(select(func.count()).select_from(Team).where(
            Team.status == TeamStatus.APPROVED)) or 0,
        "solved": sum(1 for s in subs if s.correct),
        "current_round": current.number if current else None,
        "competition_status": current.state.value if current else "idle",
        "submissions_total": len(subs),
        "correct": sum(1 for s in subs if s.correct),
        "incorrect": sum(1 for s in subs if not s.correct),
        "challenges": db.scalar(select(func.count()).select_from(Challenge)) or 0,
        "riddles": db.scalar(select(func.count()).select_from(Riddle)) or 0,
        "organisers": db.scalar(select(func.count()).select_from(Organizer)) or 0,
    }


# ------------------------------------------------------------------ teams
@router.get("/teams")
def teams(request: Request, db: Session = Depends(get_db)):
    _actor(request, db)
    rows = db.scalars(select(Team).order_by(Team.id)).all()
    return [
        {"id": t.id, "name": t.name, "college": t.college,
         "department": t.department, "semester": t.semester,
         "leader_name": t.leader_name, "leader_email": t.leader_email,
         "code": t.code, "code_active": t.code_active,
         "status": t.status.value, "score": t.score,
         "members": [{"name": m.name, "email": m.email, "mobile": m.mobile,
                      "is_leader": m.is_leader} for m in t.members]}
        for t in rows
    ]


def _team_or_404(db, team_id):
    t = db.get(Team, team_id)
    if not t:
        raise HTTPException(404, "Team not found")
    return t


@router.post("/teams/{team_id}/approve")
def approve(team_id: int, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    t = _team_or_404(db, team_id)
    t.status = TeamStatus.APPROVED
    t.code_active = True
    _log(db, actor, "team_approved", t.name)
    db.commit()
    return {"ok": True, "code": t.code}


@router.post("/teams/{team_id}/reject")
def reject(team_id: int, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    t = _team_or_404(db, team_id)
    t.status = TeamStatus.REJECTED
    _log(db, actor, "team_rejected", t.name)
    db.commit()
    return {"ok": True}


@router.post("/teams/{team_id}/code/regenerate")
def regenerate(team_id: int, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    t = _team_or_404(db, team_id)
    code = new_team_code()
    while db.scalar(select(Team.id).where(Team.code == code)):
        code = new_team_code()
    t.code = code
    t.code_active = True
    _log(db, actor, "code_regenerated", t.name)
    db.commit()
    return {"code": code}


@router.post("/teams/{team_id}/code/revoke")
def revoke(team_id: int, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    t = _team_or_404(db, team_id)
    t.code_active = False
    _log(db, actor, "code_revoked", t.name)
    db.commit()
    return {"ok": True}


@router.delete("/teams/{team_id}")
def delete_team(team_id: int, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    t = _team_or_404(db, team_id)
    _log(db, actor, "team_deleted", t.name)
    db.delete(t)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ challenges
class ChallengeIn(BaseModel):
    slug: str = Field(min_length=3, max_length=80)
    round_number: int = Field(ge=1, le=4)
    title: str = Field(min_length=2, max_length=180)
    description: str
    category: str
    difficulty: str = "Medium"
    points: int = Field(ge=1, le=10000)
    flag: str = Field(min_length=3, max_length=160)
    flag_format: str = "HQCTF{...}"
    hint1: str
    hint2: str
    solution: str
    concept: str
    attachment_name: Optional[str] = None
    attachment_text: Optional[str] = None
    prerequisite_slug: Optional[str] = None
    enabled: bool = True


@router.get("/challenges")
def all_challenges(request: Request, db: Session = Depends(get_db)):
    _actor(request, db)
    rows = db.scalars(select(Challenge).order_by(Challenge.round_number, Challenge.order_index)).all()
    return [
        {"id": c.id, "slug": c.slug, "round": c.round_number, "title": c.title,
         "description": c.description, "category": c.category,
         "difficulty": c.difficulty, "points": c.points, "flag": c.flag,
         "flag_case_sensitive": c.flag_case_sensitive, "flag_format": c.flag_format,
         "hint1": c.hint1, "hint2": c.hint2, "solution": c.solution,
         "concept": c.concept, "attachment_name": c.attachment_name,
         "attachment_text": c.attachment_text, "prerequisite": c.prerequisite_slug,
         "enabled": c.enabled}
        for c in rows
    ]


def _apply(c: Challenge, p: ChallengeIn):
    for key in ("slug", "round_number", "title", "description", "category",
                "difficulty", "points", "flag", "flag_format", "hint1", "hint2",
                "solution", "concept", "attachment_name", "attachment_text",
                "prerequisite_slug", "enabled"):
        setattr(c, key, getattr(p, key))


@router.post("/challenges", status_code=201)
def create_challenge(p: ChallengeIn, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    ensure_csrf(request)
    if db.scalar(select(Challenge.id).where(Challenge.slug == p.slug)):
        raise HTTPException(409, "Slug already exists")
    c = Challenge()
    _apply(c, p)
    c.order_index = db.scalar(select(func.coalesce(func.max(Challenge.order_index), 0))) + 1
    db.add(c)
    _log(db, actor, "challenge_created", p.slug)
    db.commit()
    return {"id": c.id}


@router.put("/challenges/{challenge_id}")
def update_challenge(challenge_id: int, p: ChallengeIn, request: Request,
                     db: Session = Depends(get_db)):
    actor = _actor(request, db)
    ensure_csrf(request)
    c = db.get(Challenge, challenge_id)
    if not c:
        raise HTTPException(404, "Challenge not found")
    _apply(c, p)
    _log(db, actor, "challenge_updated", p.slug)
    db.commit()
    return {"ok": True}


@router.delete("/challenges/{challenge_id}")
def delete_challenge(challenge_id: int, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    ensure_csrf(request)
    c = db.get(Challenge, challenge_id)
    if not c:
        raise HTTPException(404, "Challenge not found")
    _log(db, actor, "challenge_deleted", c.slug)
    db.delete(c)
    db.commit()
    return {"ok": True}


@router.post("/challenges/{challenge_id}/duplicate")
def duplicate(challenge_id: int, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    ensure_csrf(request)
    c = db.get(Challenge, challenge_id)
    if not c:
        raise HTTPException(404, "Challenge not found")
    new_slug = f"{c.slug}-copy"
    i = 2
    while db.scalar(select(Challenge.id).where(Challenge.slug == new_slug)):
        new_slug = f"{c.slug}-copy-{i}"
        i += 1
    clone = Challenge()
    for field in ("round_number", "title", "description", "category", "difficulty",
                  "points", "flag_format", "flag_case_sensitive", "hint1", "hint2",
                  "solution", "concept", "attachment_name", "attachment_text",
                  "prerequisite_slug", "enabled"):
        setattr(clone, field, getattr(c, field))
    clone.slug = new_slug
    clone.title = c.title + " (copy)"
    clone.flag = c.flag + "-copy"
    clone.order_index = c.order_index + 0.5
    db.add(clone)
    _log(db, actor, "challenge_duplicated", new_slug)
    db.commit()
    return {"id": clone.id, "slug": new_slug}


# ------------------------------------------------------------------ rounds
@router.get("/rounds")
def admin_rounds(request: Request, db: Session = Depends(get_db)):
    _actor(request, db)
    rows = db.scalars(select(Round).order_by(Round.number)).all()
    return [
        {"number": r.number, "name": r.name, "duration_minutes": r.duration_minutes,
         "state": r.state.value, "opens_at": r.opens_at.isoformat() if r.opens_at else None,
         "paused_seconds": r.paused_seconds,
         "teams": db.scalar(select(func.count()).select_from(Team).where(
             Team.status == TeamStatus.APPROVED)) or 0}
        for r in rows
    ]


def _rd(db, n):
    r = db.scalar(select(Round).where(Round.number == n))
    if not r:
        raise HTTPException(404, "Round not found")
    return r


@router.post("/rounds/{number}/start")
def start_round(number: int, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    ensure_csrf(request)
    r = _rd(db, number)
    if number > 1:
        prev = _rd(db, number - 1)
        if prev.state != RoundState.CLOSED:
            raise HTTPException(409, "Previous round must be ended first")
    if r.state in (RoundState.OPEN, RoundState.PAUSED):
        raise HTTPException(409, "Round is already running")
    if get_setting(db, "finalists_mode", "all") == "shortlist" and number == 4:
        count = int(get_setting(db, "finalist_count", 5))
        ids = [t.id for t in db.scalars(
            select(Team).where(Team.status == TeamStatus.APPROVED)
            .order_by(Team.score.desc()).limit(count)
        ).all()]
        set_setting(db, "finalist_team_ids", ids)
    r.state = RoundState.OPEN
    r.opens_at = utcnow()
    r.paused_at = None
    r.paused_seconds = 0
    r.closes_at = None
    _log(db, actor, "round_started", f"round {number}")
    db.commit()
    return {"ok": True, "state": "open", "opens_at": r.opens_at.isoformat()}


@router.post("/rounds/{number}/pause")
def pause_round(number: int, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    ensure_csrf(request)
    r = _rd(db, number)
    if r.state != RoundState.OPEN:
        raise HTTPException(409, "Only an open round can be paused")
    r.state = RoundState.PAUSED
    r.paused_at = utcnow()
    _log(db, actor, "round_paused", f"round {number}")
    db.commit()
    return {"ok": True, "state": "paused"}


@router.post("/rounds/{number}/resume")
def resume_round(number: int, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    ensure_csrf(request)
    r = _rd(db, number)
    if r.state != RoundState.PAUSED:
        raise HTTPException(409, "Only a paused round can be resumed")
    if r.paused_at:
        r.paused_seconds += int((utcnow() - as_utc(r.paused_at)).total_seconds())
    r.paused_at = None
    r.state = RoundState.OPEN
    _log(db, actor, "round_resumed", f"round {number}")
    db.commit()
    return {"ok": True, "state": "open"}


@router.post("/rounds/{number}/end")
def end_round(number: int, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    ensure_csrf(request)
    r = _rd(db, number)
    if r.state == RoundState.CLOSED:
        raise HTTPException(409, "Round already ended")
    if r.state == RoundState.PAUSED and r.paused_at:
        r.paused_seconds += int((utcnow() - as_utc(r.paused_at)).total_seconds())
    r.state = RoundState.CLOSED
    r.closes_at = utcnow()
    _log(db, actor, "round_ended", f"round {number}")
    db.commit()
    return {"ok": True, "state": "closed"}


class FinalistsIn(BaseModel):
    mode: str = Field(pattern="^(all|shortlist)$")
    count: int = Field(default=5, ge=1, le=200)


@router.post("/rounds/finalists")
def set_finalists(p: FinalistsIn, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    ensure_csrf(request)
    set_setting(db, "finalists_mode", p.mode)
    set_setting(db, "finalist_count", p.count)
    set_setting(db, "finalist_team_ids", [])
    _log(db, actor, "finalists_configured", f"{p.mode}:{p.count}")
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ scoreboard
def _scoreboard_rows(db: Session):
    teams = db.scalars(
        select(Team).where(Team.status == TeamStatus.APPROVED)
        .order_by(Team.score.desc(), Team.id)
    ).all()
    rounds = db.scalars(select(Round).order_by(Round.number)).all()
    per_round = {}
    for s in db.scalars(select(Submission).where(Submission.correct.is_(True))).all():
        ch = db.get(Challenge, s.challenge_id)
        if ch:
            per_round[(s.team_id, ch.round_number)] = per_round.get(
                (s.team_id, ch.round_number), 0) + s.points_awarded
    solved = {}
    for s in db.scalars(select(Submission).where(Submission.correct.is_(True))).all():
        solved.setdefault(s.team_id, []).append(s.challenge_id)
    rows = []
    for i, t in enumerate(teams, 1):
        rows.append({
            "rank": i, "team": t.name, "team_id": t.id,
            "members": ", ".join(m.name for m in t.members),
            "round1": per_round.get((t.id, 1), 0),
            "round2": per_round.get((t.id, 2), 0),
            "round3": per_round.get((t.id, 3), 0),
            "final": per_round.get((t.id, 4), 0),
            "total": t.score, "solved": len(set(solved.get(t.id, []))),
            "code": t.code,
        })
    return rows


@router.get("/scoreboard")
def scoreboard(request: Request, db: Session = Depends(get_db)):
    _actor(request, db)
    return {"rows": _scoreboard_rows(db)}


@router.get("/scoreboard.csv")
def scoreboard_csv(request: Request, db: Session = Depends(get_db)):
    _actor(request, db)
    rows = _scoreboard_rows(db)
    headers = ["Rank", "Team", "Members", "Round 1", "Round 2", "Round 3",
               "Final", "Total", "Solved", "Access Code"]
    data = [[r["rank"], r["team"], r["members"], r["round1"], r["round2"],
             r["round3"], r["final"], r["total"], r["solved"], r["code"]]
            for r in rows]
    return Response(to_csv(headers, data), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="hackquest2026-results.csv"'})


@router.get("/scoreboard.pdf")
def scoreboard_pdf(request: Request, db: Session = Depends(get_db)):
    _actor(request, db)
    rows = _scoreboard_rows(db)
    headers = ["Rank", "Team", "R1", "R2", "R3", "Final", "Total"]
    data = [[r["rank"], r["team"], r["round1"], r["round2"], r["round3"],
             r["final"], r["total"]] for r in rows]
    return Response(to_pdf("HACKQUEST CTF 2026 — Results", headers, data),
                    media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="hackquest2026-results.pdf"'})


@router.get("/submissions")
def submissions(request: Request, db: Session = Depends(get_db)):
    _actor(request, db)
    rows = db.scalars(select(Submission).order_by(Submission.id.desc()).limit(300)).all()
    teams = {t.id: t.name for t in db.scalars(select(Team)).all()}
    challenges = {c.id: c.title for c in db.scalars(select(Challenge)).all()}
    return [
        {"id": s.id, "team": teams.get(s.team_id, "?"),
         "challenge": challenges.get(s.challenge_id, "?"),
         "correct": s.correct, "points": s.points_awarded,
         "time": s.created_at.isoformat()}
        for s in rows
    ]


# ------------------------------------------------------------------ riddles & memes
class RiddleIn(BaseModel):
    question: str
    answer: str
    hint: str
    category: str
    break_number: int
    reveal_enabled: bool = False
    enabled: bool = True


@router.get("/riddles")
def riddles(request: Request, db: Session = Depends(get_db)):
    _actor(request, db)
    return [
        {"id": r.id, "question": r.question, "answer": r.answer, "hint": r.hint,
         "category": r.category, "break_number": r.break_number,
         "reveal_enabled": r.reveal_enabled, "enabled": r.enabled}
        for r in db.scalars(select(Riddle).order_by(Riddle.break_number, Riddle.id)).all()
    ]


@router.post("/riddles", status_code=201)
def create_riddle(p: RiddleIn, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    r = Riddle(**p.model_dump())
    db.add(r)
    _log(db, actor, "riddle_created", p.category)
    db.commit()
    return {"id": r.id}


@router.put("/riddles/{rid}")
def update_riddle(rid: int, p: RiddleIn, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    r = db.get(Riddle, rid)
    if not r:
        raise HTTPException(404, "Riddle not found")
    for k, v in p.model_dump().items():
        setattr(r, k, v)
    _log(db, actor, "riddle_updated", str(rid))
    db.commit()
    return {"ok": True}


class MemeIn(BaseModel):
    title: str
    caption: str
    image_url: Optional[str] = None
    break_number: int
    enabled: bool = True


@router.get("/memes")
def memes(request: Request, db: Session = Depends(get_db)):
    _actor(request, db)
    return [
        {"id": m.id, "title": m.title, "caption": m.caption,
         "image_url": m.image_url, "break_number": m.break_number,
         "enabled": m.enabled}
        for m in db.scalars(select(Meme).order_by(Meme.break_number, Meme.id)).all()
    ]


@router.post("/memes", status_code=201)
def create_meme(p: MemeIn, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    m = Meme(**p.model_dump())
    db.add(m)
    _log(db, actor, "meme_created", p.title)
    db.commit()
    return {"id": m.id}


@router.put("/memes/{mid}")
def update_meme(mid: int, p: MemeIn, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    m = db.get(Meme, mid)
    if not m:
        raise HTTPException(404, "Meme not found")
    for k, v in p.model_dump().items():
        setattr(m, k, v)
    _log(db, actor, "meme_updated", str(mid))
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ announcements
class AnnouncementIn(BaseModel):
    title: str
    body: str
    pinned: bool = False


@router.get("/announcements")
def admin_announcements(request: Request, db: Session = Depends(get_db)):
    _actor(request, db)
    return [
        {"id": a.id, "title": a.title, "body": a.body, "pinned": a.pinned}
        for a in db.scalars(select(Announcement).order_by(Announcement.id.desc())).all()
    ]


@router.post("/announcements", status_code=201)
def create_announcement(p: AnnouncementIn, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    a = Announcement(**p.model_dump())
    db.add(a)
    _log(db, actor, "announcement_created", p.title)
    db.commit()
    return {"id": a.id}


# ------------------------------------------------------------------ settings
@router.get("/settings")
def settings(request: Request, db: Session = Depends(get_db)):
    _actor(request, db)
    return {
        "event": get_setting(db, "event", {}),
        "schedule": get_setting(db, "schedule", []),
        "finalists_mode": get_setting(db, "finalists_mode", "all"),
        "finalist_count": get_setting(db, "finalist_count", 5),
        "score_visible_to_teams": get_setting(db, "score_visible_to_teams", False),
        "hints_free": get_setting(db, "hints_free", True),
        "hint_penalty": get_setting(db, "hint_penalty", 0),
        "riddle_bonus": get_setting(db, "riddle_bonus", 0),
        "memes_enabled": get_setting(db, "memes_enabled", True),
        "riddles_enabled": get_setting(db, "riddles_enabled", True),
        "results_published": get_setting(db, "results_published", False),
    }


class SettingsIn(BaseModel):
    event: Optional[dict] = None
    schedule: Optional[List[dict]] = None
    finalists_mode: Optional[str] = None
    finalist_count: Optional[int] = None
    score_visible_to_teams: Optional[bool] = None
    hints_free: Optional[bool] = None
    hint_penalty: Optional[int] = None
    riddle_bonus: Optional[int] = None
    memes_enabled: Optional[bool] = None
    riddles_enabled: Optional[bool] = None


@router.put("/settings")
def update_settings(p: SettingsIn, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    ensure_csrf(request)
    for key, value in p.model_dump(exclude_none=True).items():
        set_setting(db, key, value)
    _log(db, actor, "settings_updated", ", ".join(p.model_dump(exclude_none=True)))
    db.commit()
    return {"ok": True}


@router.post("/results/publish")
def publish_results(request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    ensure_csrf(request)
    set_setting(db, "results_published", True)
    _log(db, actor, "results_published")
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ audit & accounts
@router.get("/audit")
def audit_log(request: Request, db: Session = Depends(get_db)):
    _actor(request, db)
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(300)).all()
    return [
        {"id": a.id, "actor_type": a.actor_type, "actor_id": a.actor_id,
         "action": a.action, "detail": a.detail, "time": a.created_at.isoformat()}
        for a in rows
    ]


@router.get("/accounts")
def accounts(request: Request, db: Session = Depends(get_db)):
    _actor(request, db)
    return [
        {"username": o.username, "full_name": o.full_name, "role": o.role,
         "must_change_password": o.must_change_password}
        for o in db.scalars(select(Organizer).order_by(Organizer.id)).all()
    ]


@router.post("/accounts/{username}/reset-password")
def reset_password(username: str, request: Request, db: Session = Depends(get_db)):
    actor = _actor(request, db)
    ensure_csrf(request)
    from ..security import new_temp_password
    o = db.scalar(select(Organizer).where(Organizer.username == username))
    if not o:
        raise HTTPException(404, "Organiser not found")
    temp = new_temp_password()
    o.password_hash = hash_password(temp)
    o.must_change_password = True
    _log(db, actor, "organizer_password_reset", username)
    db.commit()
    return {"temporary_password": temp}
