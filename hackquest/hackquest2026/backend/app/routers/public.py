"""Unauthenticated event information (never contains flags or solutions)."""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Announcement, Challenge, Meme, Riddle, Round
from ..seed import get_setting

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/health")
def health():
    return {"status": "ok", "event": "HACKQUEST CTF 2026"}


@router.get("/event")
def event(db: Session = Depends(get_db)):
    return {
        "event": get_setting(db, "event", {}),
        "schedule": get_setting(db, "schedule", []),
        "marquee": get_setting(db, "marquee", ""),
        "organisers": "Pragyan × IEEE-CS KLEIT Chapter",
    }


@router.get("/results")
def results(db: Session = Depends(get_db)):
    if not get_setting(db, "results_published", False):
        raise HTTPException(404, "Results are not published yet")
    from .admin import _scoreboard_rows
    return {"rows": _scoreboard_rows(db)}


@router.get("/rounds")
def rounds(db: Session = Depends(get_db)):
    return [
        {"number": r.number, "name": r.name,
         "duration_minutes": r.duration_minutes, "state": r.state.value}
        for r in db.scalars(select(Round).order_by(Round.number)).all()
    ]


@router.get("/announcements")
def announcements(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Announcement).order_by(Announcement.pinned.desc(), Announcement.id.desc()).limit(20)
    ).all()
    return [{"title": a.title, "body": a.body, "pinned": a.pinned} for a in rows]


@router.get("/break/{number}")
def break_content(number: int, db: Session = Depends(get_db)):
    riddle = db.scalar(
        select(Riddle).where(Riddle.break_number == number, Riddle.enabled.is_(True))
    )
    meme = db.scalar(
        select(Meme).where(Meme.break_number == number, Meme.enabled.is_(True))
    )
    return {
        "riddle": ({"id": riddle.id, "question": riddle.question, "hint": riddle.hint,
                    "category": riddle.category, "reveal_enabled": riddle.reveal_enabled}
                   if riddle else None),
        "meme": ({"title": meme.title, "caption": meme.caption,
                  "image_url": meme.image_url} if meme else None),
    }


@router.get("/reveal/{riddle_id}")
def reveal(riddle_id: int, db: Session = Depends(get_db)):
    row = db.get(Riddle, riddle_id)
    if not row or not row.reveal_enabled:
        raise HTTPException(403, "Answer reveal is not enabled by the organisers")
    return {"answer": row.answer}


@router.get("/attachments/{slug}")
def attachment(slug: str, db: Session = Depends(get_db)):
    ch = db.scalar(select(Challenge).where(Challenge.slug == slug))
    if not ch or not ch.attachment_text:
        raise HTTPException(404, "Attachment not found")
    return Response(
        content=ch.attachment_text,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{ch.attachment_name or "challenge.txt"}"'},
    )
