"""Participant APIs: dashboard, challenges, hints and flag submissions."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..audit import record
from ..db import get_db
from ..deps import ensure_csrf, rate_limit, require_team
from ..models import (Announcement, Challenge, HintUse, Round, RoundState,
                      Submission, TeamStatus)
from ..security import as_utc, constant_time_eq, utcnow
from ..seed import get_setting

router = APIRouter(prefix="/api/team", tags=["team"])


def _solved_ids(db: Session, team_id: int) -> set:
    return set(db.scalars(
        select(Submission.challenge_id).where(
            Submission.team_id == team_id, Submission.correct.is_(True)
        )
    ).all())


def _remaining(rd: Round) -> int | None:
    if rd.state not in (RoundState.OPEN, RoundState.PAUSED):
        return None
    if not rd.opens_at:
        return rd.duration_minutes * 60
    end = as_utc(rd.opens_at).timestamp() + rd.duration_minutes * 60
    if rd.state == RoundState.PAUSED and rd.paused_at:
        end += (utcnow() - as_utc(rd.paused_at)).total_seconds()
    return max(0, int(end - utcnow().timestamp() - rd.paused_seconds))


def _round_allowed(db: Session, team, rd: Round) -> bool:
    if rd.state in (RoundState.OPEN, RoundState.PAUSED, RoundState.CLOSED):
        if rd.number == 4 and get_setting(db, "finalists_mode", "all") == "shortlist":
            finalists = get_setting(db, "finalist_team_ids", [])
            if team.id not in finalists:
                return False
        return True
    return False


@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    actor = require_team(request, db)
    team = actor.obj
    solved = _solved_ids(db, team.id)
    return {
        "team": {
            "id": team.id, "name": team.name, "code": team.code,
            "code_active": team.code_active, "status": team.status.value,
            "college": team.college, "department": team.department,
            "semester": team.semester,
            "members": [{"name": m.name, "email": m.email,
                         "mobile": m.mobile, "is_leader": m.is_leader}
                        for m in team.members],
        },
        "score": team.score,
        "solved": len(solved),
        "total": db.query(Challenge).filter(Challenge.enabled.is_(True)).count(),
        "score_visible": get_setting(db, "score_visible_to_teams", False),
        "announcements": [
            {"title": a.title, "body": a.body}
            for a in db.scalars(
                select(Announcement).order_by(Announcement.id.desc()).limit(5)
            ).all()
        ],
    }


@router.get("/state")
def state(request: Request, db: Session = Depends(get_db)):
    """Lightweight polling endpoint used by the dashboard timer."""
    actor = require_team(request, db)
    rounds = []
    for rd in db.scalars(select(Round).order_by(Round.number)).all():
        rounds.append({
            "number": rd.number, "name": rd.name, "state": rd.state.value,
            "remaining_seconds": _remaining(rd),
            "allowed": _round_allowed(db, actor.obj, rd),
        })
    solved = _solved_ids(db, actor.obj.id)
    return {
        "server_now": utcnow().isoformat(),
        "rounds": rounds, "solved": sorted(solved),
        "score": actor.obj.score,
    }


@router.get("/challenges")
def challenges(request: Request, db: Session = Depends(get_db)):
    actor = require_team(request, db)
    solved = _solved_ids(db, actor.obj.id)
    rounds = {r.number: r for r in db.scalars(select(Round)).all()}
    result = []
    for ch in db.scalars(select(Challenge).order_by(Challenge.round_number, Challenge.order_index)).all():
        if not ch.enabled:
            continue
        rd = rounds.get(ch.round_number)
        allowed = rd is not None and _round_allowed(db, actor.obj, rd)
        result.append({
            "slug": ch.slug, "round": ch.round_number, "order": ch.order_index,
            "title": ch.title, "category": ch.category, "difficulty": ch.difficulty,
            "points": ch.points, "flag_format": ch.flag_format,
            "status": ("solved" if ch.id in solved else
                       "available" if allowed and rd.state == RoundState.OPEN else
                       "review" if allowed and rd.state == RoundState.CLOSED else "locked"),
            "hint_count": 2,
            "attachment_name": ch.attachment_name,
            "prerequisite": ch.prerequisite_slug,
        })
    return {"challenges": result, "solved": sorted(solved)}


@router.get("/challenge/{slug}")
def challenge_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    actor = require_team(request, db)
    ch = db.scalar(select(Challenge).where(Challenge.slug == slug, Challenge.enabled.is_(True)))
    if not ch:
        raise HTTPException(404, "Challenge not found")
    rd = db.get(Round, ch.round_number)
    if not _round_allowed(db, actor.obj, rd):
        raise HTTPException(403, "This round is locked")
    solved = ch.id in _solved_ids(db, actor.obj.id)
    used = set(db.scalars(select(HintUse.hint_index).where(
        HintUse.team_id == actor.id, HintUse.challenge_id == ch.id
    )).all())
    return {
        "slug": ch.slug, "title": ch.title, "description": ch.description,
        "round": ch.round_number, "category": ch.category,
        "difficulty": ch.difficulty, "points": ch.points,
        "flag_format": ch.flag_format, "solved": solved,
        "attachment_name": ch.attachment_name,
        "hints": [
            {"index": 1, "text": ch.hint1, "used": 1 in used},
            {"index": 2, "text": ch.hint2, "used": 2 in used},
        ],
        "hint_penalty": get_setting(db, "hint_penalty", 0),
    }


@router.post("/hint/{slug}/{index}")
def use_hint(slug: str, index: int, request: Request, db: Session = Depends(get_db)):
    actor = require_team(request, db)
    ensure_csrf(request)
    if index not in (1, 2):
        raise HTTPException(400, "Invalid hint index")
    ch = db.scalar(select(Challenge).where(Challenge.slug == slug))
    if not ch:
        raise HTTPException(404, "Challenge not found")
    existing = db.scalar(select(HintUse).where(
        HintUse.team_id == actor.id, HintUse.challenge_id == ch.id,
        HintUse.hint_index == index
    ))
    if not existing:
        db.add(HintUse(team_id=actor.id, challenge_id=ch.id, hint_index=index))
        record(db, "team", actor.id, "hint_used", f"{slug} hint {index}")
        db.commit()
    return {"ok": True}


class SubmitIn(BaseModel):
    flag: str = Field(min_length=3, max_length=200)


@router.post("/submit")
def submit(payload: SubmitIn, request: Request, db: Session = Depends(get_db)):
    actor = require_team(request, db)
    ensure_csrf(request)
    rate_limit(f"flag:{actor.id}", limit=12, window=60)
    slug = request.headers.get("x-challenge")
    if not slug:
        raise HTTPException(400, "Missing challenge header")
    ch = db.scalar(select(Challenge).where(Challenge.slug == slug, Challenge.enabled.is_(True)))
    if not ch:
        raise HTTPException(404, "Challenge not found")
    rd = db.get(Round, ch.round_number)
    if not rd or rd.state != RoundState.OPEN:
        raise HTTPException(409, "Challenge is not accepting submissions")
    if not _round_allowed(db, actor.obj, rd):
        raise HTTPException(403, "This round is locked for your team")
    if ch.id in _solved_ids(db, actor.id):
        return {"correct": False, "message": "Challenge already solved", "already_solved": True}

    candidate = payload.flag.strip()
    expected = ch.flag
    correct = constant_time_eq(candidate, expected) if ch.flag_case_sensitive else \
        constant_time_eq(candidate.lower(), expected.lower())

    used_hints = db.scalar(
        select(func.count()).select_from(HintUse).where(
            HintUse.team_id == actor.id, HintUse.challenge_id == ch.id
        )
    ) or 0
    penalty = get_setting(db, "hint_penalty", 0) * used_hints
    awarded = max(0, ch.points - int(penalty)) if correct else 0
    sub = Submission(team_id=actor.id, challenge_id=ch.id,
                     submitted_flag=candidate[:160], correct=correct,
                     points_awarded=awarded)
    db.add(sub)
    if correct:
        actor.obj.score += awarded
    record(db, "team", actor.id, "flag_correct" if correct else "flag_incorrect", slug)
    db.commit()
    return {
        "correct": correct,
        "message": "Correct flag! Points awarded." if correct else "Incorrect flag.",
        "points": awarded,
        "solved": correct,
    }


@router.get("/submissions")
def submissions(request: Request, db: Session = Depends(get_db)):
    actor = require_team(request, db)
    rows = db.scalars(
        select(Submission).where(Submission.team_id == actor.id)
        .order_by(Submission.id.desc()).limit(100)
    ).all()
    slugs = {c.id: c.title for c in db.scalars(select(Challenge)).all()}
    return [
        {"challenge": slugs.get(s.challenge_id, "Unknown"),
         "correct": s.correct, "points": s.points_awarded,
         "time": s.created_at.isoformat()}
        for s in rows
    ]
