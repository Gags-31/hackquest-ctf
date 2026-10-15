"""Public leaderboard and results endpoints."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_actor, hint_penalty, scoring_mode, setting
from ..scoring import leaderboard, max_possible

router = APIRouter(prefix="/api", tags=["public"])


@router.get("/leaderboard")
def board(request: Request, db: Session = Depends(get_db)):
    mode = scoring_mode(db)
    frozen = setting(db, "results_frozen", "0") == "1"
    published = setting(db, "results_published", "0") == "1"
    rows = leaderboard(db, mode, hint_penalty(db), frozen=frozen)

    # Hide individual scores until the freeze when the organizer asks for it.
    if not frozen:
        for r in rows:
            r.pop("last_solve_at", None)

    actor = current_actor(request, db)
    me = None
    if actor and actor.is_team:
        me = next((r for r in rows if r["team_code"] == actor.obj.team_code), None)

    return {
        "rows": rows,
        "max_possible": max_possible(mode),
        "scoring_mode": mode.value,
        "frozen": frozen,
        "published": published,
        "me": me,
        "event_timezone": setting(db, "event_timezone", "Asia/Kolkata"),
    }


@router.get("/results")
def results(db: Session = Depends(get_db)):
    published = setting(db, "results_published", "0") == "1"
    mode = scoring_mode(db)
    if not published:
        return {"published": False,
                "message": "Results will be published once verification is complete."}
    rows = leaderboard(db, mode, hint_penalty(db), frozen=True)
    return {"published": True, "rows": rows,
            "max_possible": max_possible(mode), "scoring_mode": mode.value}