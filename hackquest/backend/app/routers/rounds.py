"""Rounds, challenges, submissions, hints, unlocks and proctoring."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..audit import record
from ..config import settings
from ..db import get_db
from ..deps import (current_actor, hint_penalty, rate_limit, require_csrf,
                    require_team, scoring_mode, setting)
from ..models import (Challenge, HintUse, Round, RoundState, RoundUnlock,
                      ScoringMode, Submission, Team, TeamStatus, Violation)
from ..sandbox import (CodeRejection, analyze_code, check_structured_patch,
                       parse_json_field)
from ..scoring import normalized_weight, scoring_summary
from ..validators import norm_loose, validate

router = APIRouter(prefix="/api", tags=["competition"])


class SubmitIn(BaseModel):
    challenge_key: str = Field(min_length=3, max_length=64)
    answer: str = Field(default="", max_length=8000)


class UnlockIn(BaseModel):
    round_number: int
    code: str = Field(default="", max_length=300)


class ViolationIn(BaseModel):
    kind: str = Field(max_length=60)
    detail: str = Field(default="", max_length=255)


def _team_state(db: Session, team: Team) -> dict:
    return {
        "disqualified": team.status == TeamStatus.DISQUALIFIED,
        "competition": setting(db, "competition_state", "pending"),
        "results_frozen": setting(db, "results_frozen", "0") == "1",
        "results_published": setting(db, "results_published", "0") == "1",
    }


def _round_view(db: Session, rd: Round, team: Team | None) -> dict:
    done = 0
    if team:
        done = db.query(func.count(Submission.id)).filter(
            Submission.team_id == team.id,
            Submission.round_number == rd.number,
            Submission.correct.is_(True)).scalar()
    return {
        "number": rd.number, "slug": rd.slug, "name": rd.name, "blurb": rd.blurb,
        "state": rd.state.value,
        "challenges_total": len(rd.challenges),
        "challenges_solved": done,
        # unlock_code is deliberately never included.
    }


def _challenge_view(db: Session, ch: Challenge, team: Team | None,
                    review: bool = False) -> dict:
    hints = db.query(HintUse).filter_by(team_id=team.id,
                                         challenge_key=ch.key).count() if team else 0
    data = {
        "key": ch.key, "title": ch.title, "category": ch.category,
        "difficulty": ch.difficulty, "description": ch.description,
        "answer_format": ch.answer_format, "initial_clue": ch.initial_clue,
        "points": None, "hints_used": hints,
        "hint_penalty": hint_penalty(db),
    }
    if review:
        # Post-competition review only.
        data["explanation"] = ch.explanation
        data["hints"] = [h for h in (ch.hint1, ch.hint2, ch.hint3) if h]
    return data


def _hints_allowed(ch: Challenge, team: Team | None) -> dict:
    return {"available": 3, "unlocked": 0}


# ------------------------------------------------------------------ overview
@router.get("/rounds")
def list_rounds(request: Request, db: Session = Depends(get_db)):
    actor = current_actor(request, db)
    team = actor.obj if (actor and actor.is_team) else None
    st = _team_state(db, team) if team else {}
    rounds = []
    for rd in db.query(Round).order_by(Round.number).all():
        unlocked = False
        if team and rd.state == RoundState.OPEN:
            if rd.number == 1:
                unlocked = True
            else:
                prev = db.query(RoundUnlock).filter_by(
                    team_id=team.id, round_number=rd.number - 1).first()
                unlocked = prev is not None
        rounds.append({**_round_view(db, rd, team), "unlocked": unlocked})
    mode = scoring_mode(db)
    return {
        "rounds": rounds,
        "scoring": scoring_summary(mode),
        "state": st,
        "event_datetime": setting(db, "event_datetime", ""),
        "event_timezone": setting(db, "event_timezone", "Asia/Kolkata"),
    }


# ------------------------------------------------------------------ challenges
@router.get("/rounds/{slug}")
def round_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    actor = current_actor(request, db)
    team = actor.obj if (actor and actor.is_team) else None
    rd = db.query(Round).filter_by(slug=slug).first()
    if not rd:
        raise HTTPException(404, "Round not found.")

    solved = set()
    hints_used = {}
    if team:
        rows = db.query(Submission).filter_by(team_id=team.id,
                                              round_number=rd.number).all()
        solved = {s.challenge_key for s in rows if s.correct}
        hints_used = {s.challenge_key: s.hint_used for s in rows}

    view = _round_view(db, rd, team)
    challenges = []
    review = rd.state == RoundState.CLOSED
    for ch in sorted(rd.challenges, key=lambda c: c.order_index):
        cv = _challenge_view(db, ch, team, review=review)
        cv["solved"] = ch.key in solved
        cv["points"] = normalized_weight(rd.number, scoring_mode(db))
        cv["hints"] = [h for h in (ch.hint1, ch.hint2, ch.hint3) if h] if review else []
        cv["hints_unlocked"] = 0
        challenges.append(cv)
    view["challenges"] = challenges
    view["explanation"] = rd.explanation if review else None
    return view


@router.post("/challenges/{key}/hint")
def request_hint(key: str, request: Request, db: Session = Depends(get_db)):
    actor = require_team(request, db)
    team = actor.obj
    ip = request.client.host if request.client else "anon"
    rate_limit(f"hint:{team.id}:{ip}", settings.HINT_RATE_LIMIT, 300)

    ch = db.query(Challenge).filter_by(key=key).first()
    if not ch:
        raise HTTPException(404, "Challenge not found.")
    rd = ch.round
    if rd.state != RoundState.OPEN:
        raise HTTPException(403, "This round is not open.")
    if team.status == TeamStatus.DISQUALIFIED:
        raise HTTPException(403, "Team is disqualified.")

    existing = db.query(HintUse).filter_by(team_id=team.id, challenge_key=key).all()
    if len(existing) >= 3:
        raise HTTPException(400, "All hints for this challenge are already revealed.")
    number = len(existing) + 1
    db.add(HintUse(team_id=team.id, challenge_key=key, hint_number=number))
    db.commit()
    text = {1: ch.hint1, 2: ch.hint2, 3: ch.hint3}[number]
    return {"hint": text, "hint_number": number,
            "penalty": hint_penalty(db),
            "note": "Hints are free by default; the organizer may configure a penalty."}


# ------------------------------------------------------------------ submissions
def _maybe_unlock(db: Session, team: Team, rd: Round, request: Request) -> dict | None:
    total = len(rd.challenges)
    solved = db.query(func.count(func.distinct(Submission.challenge_key))).filter(
        Submission.team_id == team.id, Submission.round_number == rd.number,
        Submission.correct.is_(True)).scalar()
    if solved < total:
        return None
    existing = db.query(RoundUnlock).filter_by(team_id=team.id,
                                              round_number=rd.number).first()
    if existing:
        return {"round": rd.number, "code": rd.unlock_code, "already": True}
    db.add(RoundUnlock(team_id=team.id, round_number=rd.number,
                       code_used="generated"))
    db.commit()
    record(db, actor=team.name, action="round.unlocked",
           target=f"round{rd.number}", request=request)
    return {"round": rd.number, "code": rd.unlock_code, "already": False}


@router.post("/submit")
def submit(payload: SubmitIn, request: Request, db: Session = Depends(get_db)):
    actor = require_team(request, db)
    team = actor.obj
    st = _team_state(db, team)
    if team.status == TeamStatus.DISQUALIFIED:
        raise HTTPException(403, "This team is disqualified.")
    if st["competition"] not in ("running",):
        raise HTTPException(403, "The competition is not running.")

    ip = request.client.host if request.client else "anon"
    rate_limit(f"sub:{team.id}:{ip}", settings.SUBMIT_RATE_LIMIT, 60)

    ch = db.query(Challenge).filter_by(key=payload.challenge_key).first()
    if not ch:
        raise HTTPException(404, "Challenge not found.")
    rd = ch.round
    if rd.state != RoundState.OPEN:
        raise HTTPException(403, "This round is not open.")

    prior = db.query(Submission).filter_by(team_id=team.id,
                                           challenge_key=ch.key).first()
    if prior and prior.correct:
        return {"correct": True, "already_accepted": True, "points": prior.points_awarded,
                "message": "This challenge is already solved."}

    mode = scoring_mode(db)
    penalty = hint_penalty(db)
    hints = db.query(HintUse).filter_by(team_id=team.id,
                                        challenge_key=ch.key).count()

    # ---- Round 5: safe structured / static analysis path (never executes code)
    if ch.is_code_challenge:
        correct, segment = False, ""
        detail = None
        raw = (payload.answer or "").strip()
        if raw.startswith("{"):
            try:
                patch = parse_json_field(raw)
                result = check_structured_patch(patch)
                correct = result["correct"]
                detail = result
                if correct:
                    segment = ch.segment
            except CodeRejection as e:
                raise HTTPException(422, str(e))
        else:
            try:
                info = analyze_code(raw)
                detail = info
                cmp_ = info.get("comparator") or {}
                if cmp_.get("rhs") == 0:
                    correct, segment = True, ch.segment
                else:
                    correct, segment = False, ""
            except CodeRejection as e:
                raise HTTPException(422, str(e))
        normalized = norm_loose(raw)[:120]
    else:
        correct, segment = validate(ch.key, payload.answer)
        normalized = norm_loose(payload.answer)[:120]
        detail = None

    points = 0
    if correct:
        points = max(0, normalized_weight(rd.number, mode) - penalty * hints)

    if prior:
        prior.answer = (payload.answer or "")[:200]
        prior.normalized = normalized
        prior.correct = correct
        prior.points_awarded = points
        prior.hint_used = hints
        prior.attempt_number = (prior.attempt_number or 1) + 1
        prior.at = datetime.now(timezone.utc)
        sub = prior
    else:
        sub = Submission(team_id=team.id, challenge_key=ch.key,
                         round_number=rd.number, answer=(payload.answer or "")[:200],
                         normalized=normalized, correct=correct, points_awarded=points,
                         hint_used=hints, attempt_number=1)
        db.add(sub)
    db.commit()

    unlocked = _maybe_unlock(db, team, rd, request) if correct else None

    record(db, actor=team.name, action="challenge.submit",
           target=ch.key, detail=f"correct={correct}", request=request)

    return {
        "correct": correct,
        "points": points,
        "attempts": sub.attempt_number,
        "already_accepted": bool(prior and prior.correct),
        "unlocked": unlocked,
        "test_detail": detail,
    }


# ------------------------------------------------------------------ unlocks
@router.post("/unlock")
def unlock(payload: UnlockIn, request: Request, db: Session = Depends(get_db)):
    actor = require_team(request, db)
    team = actor.obj
    rate_limit(f"unlock:{team.id}", 20, 300)
    rd = db.query(Round).filter_by(number=payload.round_number).first()
    if not rd:
        raise HTTPException(404, "Round not found.")
    if rd.state != RoundState.OPEN:
        raise HTTPException(403, "That round is not open.")

    existing = db.query(RoundUnlock).filter_by(team_id=team.id,
                                              round_number=payload.round_number).first()
    if existing:
        return {"ok": True, "round": rd.number, "code": rd.unlock_code,
                "already": True}

    from ..security import constant_time_eq
    if not constant_time_eq((payload.code or "").strip(), rd.unlock_code):
        record(db, actor=team.name, action="unlock.failed",
               target=f"round{payload.round_number}", request=request)
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "That unlock code is not valid for this round.")

    db.add(RoundUnlock(team_id=team.id, round_number=rd.number,
                       code_used=payload.code[:200]))
    db.commit()
    record(db, actor=team.name, action="unlock.ok",
           target=f"round{payload.round_number}", request=request)
    return {"ok": True, "round": rd.number, "code": rd.unlock_code}


# ------------------------------------------------------------------ proctoring
@router.post("/violation")
def report_violation(payload: ViolationIn, request: Request, db: Session = Depends(get_db)):
    actor = current_actor(request, db)
    if not actor or not actor.is_team:
        raise HTTPException(401, "Sign in as a team.")
    team = actor.obj
    if team.status == TeamStatus.DISQUALIFIED:
        return {"ok": True, "violations": 0, "disqualified": True,
                "limit": settings.PROCTOR_VIOLATION_LIMIT}

    # Server-authoritative counting: never trust a client-supplied total.
    kind = payload.kind if payload.kind in {
        "tab-hidden", "window-blur", "exit-fullscreen",
        "page-exit", "heartbeat-missed"} else "unknown"
    db.add(Violation(team_id=team.id, kind=kind, detail=payload.detail[:255]))
    db.commit()

    live = db.query(func.count(Violation.id)).filter(
        Violation.team_id == team.id, Violation.forgiven.is_(False)).scalar()
    limit = settings.PROCTOR_VIOLATION_LIMIT
    if live >= limit and team.status != TeamStatus.DISQUALIFIED:
        team.status = TeamStatus.DISQUALIFIED
        db.commit()
        record(db, actor=team.name, action="team.auto_disqualified",
               target=team.team_code, detail=f"violations={live}", request=request)

    return {"ok": True, "violations": live, "limit": limit,
            "disqualified": live >= limit,
            "notice": "Three verified violations disqualify a team. "
                      "Contact an organizer to appeal." if live >= limit else None}


@router.post("/heartbeat")
def heartbeat(request: Request, db: Session = Depends(get_db)):
    actor = current_actor(request, db)
    if not actor:
        raise HTTPException(401, "Sign in.")
    return {"ok": True, "server_time": datetime.now(timezone.utc).isoformat(),
            "team": actor.name}