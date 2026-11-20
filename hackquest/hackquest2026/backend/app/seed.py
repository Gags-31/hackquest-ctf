"""Seed the 2026 event: rounds, 48 challenges, riddles, memes and settings."""
import json

from sqlalchemy.orm import Session

from . import content
from .models import (
    Announcement, Challenge, Meme, Organizer, Riddle, Round, Setting,
)
from .security import hash_password, new_temp_password


def set_setting(db: Session, key: str, value) -> None:
    row = db.get(Setting, key)
    if row is None:
        db.add(Setting(key=key, value=value if isinstance(value, str) else json.dumps(value)))
    else:
        row.value = value if isinstance(value, str) else json.dumps(value)


def get_setting(db: Session, key: str, default=None):
    row = db.get(Setting, key)
    if row is None:
        return default
    try:
        return json.loads(row.value)
    except (ValueError, TypeError):
        return row.value


def seed_rounds(db: Session) -> None:
    for item in content.ROUNDS:
        rd = db.query(Round).filter_by(number=item["number"]).first()
        if rd is None:
            rd = Round(number=item["number"])
            db.add(rd)
        rd.name = item["name"]
        rd.duration_minutes = item["duration_minutes"]
    db.flush()


def seed_challenges(db: Session, refresh_flags: bool = False) -> None:
    for idx, item in enumerate(content.CHALLENGES):
        ch = db.query(Challenge).filter_by(slug=item["slug"]).first()
        if ch is None:
            ch = Challenge(slug=item["slug"])
            db.add(ch)
        ch.round_number = item["round"]
        ch.order_index = idx
        ch.title = item["title"]
        ch.description = item["description"]
        ch.category = item["category"]
        ch.difficulty = item["difficulty"]
        ch.points = item["points"]
        ch.flag = item["flag"]
        ch.flag_format = "HQCTF{...}"
        ch.flag_case_sensitive = True
        ch.hint1 = item["hint1"]
        ch.hint2 = item["hint2"]
        ch.solution = item["solution"]
        ch.concept = item["concept"]
        ch.attachment_name = item["attachment"][0] if item["attachment"] else None
        ch.attachment_text = item["attachment"][1] if item["attachment"] else None
        ch.prerequisite_slug = item["prerequisite"]
        ch.enabled = True
    db.flush()


def seed_extras(db: Session) -> None:
    if db.query(Riddle).count() == 0:
        for i, (q, a, h, cat, br) in enumerate(content.RIDDLES):
            db.add(Riddle(question=q, answer=a, hint=h, category=cat,
                          break_number=br, enabled=True))
    if db.query(Meme).count() == 0:
        for m in content.MEMES:
            db.add(Meme(**m))
    if db.query(Announcement).count() == 0:
        db.add(Announcement(
            title="Welcome to HACKQUEST CTF 2026",
            body="Rounds unlock together from the organiser console. Read the rules, form a team of 2–4, and decode responsibly.",
            pinned=True,
        ))
    for key, value in {
        "event": content.EVENT,
        "schedule": content.SCHEDULE,
        "marquee": content.MARQUEE,
        "finalists_mode": "all",
        "score_visible_to_teams": False,
        "hints_free": True,
        "hint_penalty": 0,
        "riddle_bonus": 0,
        "memes_enabled": True,
        "riddles_enabled": True,
    }.items():
        set_setting(db, key, value)
    db.flush()


def bootstrap_organizers(db: Session, passwords: dict | None = None) -> dict:
    """Create the two organiser accounts. Passwords are never stored in source."""
    passwords = passwords or {}
    specs = [
        ("pragyan_lead", "Pragyan Lead Organiser", "pragyan.lead@hackquest.local", "primary", "ORG1_PASSWORD"),
        ("ieee_lead", "IEEE-CS KLEIT Co-Organiser", "ieee.lead@hackquest.local", "co-organizer", "ORG2_PASSWORD"),
    ]
    issued = {}
    for username, full_name, email, role, env_key in specs:
        if db.query(Organizer).filter_by(username=username).first():
            continue
        import os
        password = passwords.get(username) or os.environ.get(env_key) or new_temp_password()
        db.add(Organizer(
            username=username, email=email, full_name=full_name, role=role,
            password_hash=hash_password(password), must_change_password=True,
        ))
        issued[username] = password
    db.flush()
    return issued


def run(refresh: bool = True) -> dict:
    from .db import SessionLocal
    db = SessionLocal()
    try:
        seed_rounds(db)
        seed_challenges(db, refresh_flags=refresh)
        seed_extras(db)
        issued = bootstrap_organizers(db)
        db.commit()
        return {"issued_passwords": issued}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
