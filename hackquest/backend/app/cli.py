"""Organizer bootstrap and maintenance CLI.

Usage:
    python -m app.cli bootstrap --username lead --email a@b.c --name "Lead" [--second]
    python -m app.cli seed
    python -m app.cli verify-keys
    python -m app.cli set-scoring tier|normalized
    python -m app.cli reset-event
"""
import argparse
import getpass
import sys

from .db import SessionLocal, init_db
from .models import AppSetting, Challenge, Organizer, Round, ScoringMode, Team
from .scoring import TIER_MAX, max_possible
from .security import hash_password
from .validators import VALIDATORS


def cmd_seed(_args):
    from .seed import run
    print("seeded:", run())


def cmd_bootstrap(args):
    init_db()
    db = SessionLocal()
    role = "admin" if db.query(Organizer).count() == 0 else "moderator"
    username = args.username or input("username: ").strip()
    if db.query(Organizer).filter_by(username=username).first():
        print(f"organizer '{username}' already exists")
        db.close()
        return 1
    email = args.email or input("email: ").strip()
    full_name = args.name or input("full name: ").strip()
    pwd = args.password or getpass.getpass("password (min 12 chars): ")
    if len(pwd) < 12:
        print("password must be at least 12 characters")
        db.close()
        return 1
    db.add(Organizer(username=username, email=email, full_name=full_name,
                     role=role, password_hash=hash_password(pwd),
                     must_change_password=True))
    db.commit()
    db.close()
    print(f"created {role} organizer '{username}'. "
          f"A password change is required on first sign-in.")
    return 0


def cmd_verify_keys(_args):
    """Recompute every answer key and compare it with what is stored.

    Feeds each validator its canonical *submission* (what a participant types),
    not the stored key - these differ for base-36, Base64 and cipher rounds.
    """
    from .seed import CHALLENGES, R5_CHALLENGE, SAMPLE_SUBMISSIONS
    from .sandbox import check_structured_patch

    db = SessionLocal()
    seed_keys = {c[0]: c[12] for c in CHALLENGES}
    seed_keys[R5_CHALLENGE["key"]] = R5_CHALLENGE["answer"]

    failures = 0
    for key, want in seed_keys.items():
        stored = db.query(Challenge).filter_by(key=key).first()
        problems = []
        if not stored:
            problems.append("not seeded")
        else:
            if stored.answer_key != want:
                problems.append(f"answer_key {stored.answer_key!r} != {want!r}")
            if not stored.segment:
                problems.append("empty segment")
        # Round 5 uses the sandbox, not a plain validator.
        if key.startswith("hq_r5"):
            import json as _json
            ok = check_structured_patch(_json.loads(SAMPLE_SUBMISSIONS[key]))["correct"]
        else:
            ok, seg = VALIDATORS[key](SAMPLE_SUBMISSIONS[key])
            if not ok:
                problems.append("sample submission rejected")
            elif stored and seg != stored.segment:
                problems.append(f"segment {seg!r} != {stored.segment!r}")
        status = "OK  " if not problems else "FAIL"
        if problems:
            failures += 1
        print(f"{status} {key}: " + ("; ".join(problems) if problems else "key and segment agree"))
    db.close()
    print(f"\n{15 - failures}/15 challenges verified")
    return 1 if failures else 0


def cmd_set_scoring(args):
    db = SessionLocal()
    row = db.query(AppSetting).filter_by(key="scoring_mode").first()
    if not row:
        row = AppSetting(key="scoring_mode", value="")
        db.add(row)
    row.value = args.mode
    db.commit()
    mode = ScoringMode(args.mode)
    print(f"scoring_mode = {mode.value}, max possible = {max_possible(mode)}")
    db.close()
    return 0


def cmd_reset_event(_args):
    db = SessionLocal()
    for t in ("submissions", "hint_uses", "round_unlocks", "violations",
              "teams", "audit_log"):
        db.execute(f"DELETE FROM {t}")
    for rd in db.query(Round).all():
        rd.state = rd.state.__class__.LOCKED
    for key, val in [("competition_state", "pending"), ("results_frozen", "0"),
                     ("results_published", "0")]:
        row = db.query(AppSetting).filter_by(key=key).first()
        if row:
            row.value = val
    db.commit()
    db.close()
    print("event reset: teams, scores, unlocks and violations cleared; rounds locked")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="app.cli", description="HackQuest CTF admin CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("bootstrap", help="create an organizer account")
    b.add_argument("--username")
    b.add_argument("--email")
    b.add_argument("--name")
    b.add_argument("--password")
    b.set_defaults(fn=cmd_bootstrap)

    sub.add_parser("seed", help="seed rounds, challenges and answer keys").set_defaults(fn=cmd_seed)
    sub.add_parser("verify-keys", help="verify all stored answer keys").set_defaults(fn=cmd_verify_keys)

    sc = sub.add_parser("set-scoring", help="set scoring mode")
    sc.add_argument("mode", choices=[ScoringMode.TIER.value, ScoringMode.NORMALIZED.value])
    sc.set_defaults(fn=cmd_set_scoring)

    sub.add_parser("reset-event", help="clear all event data").set_defaults(fn=cmd_reset_event)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())