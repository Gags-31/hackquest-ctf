"""Server-side scoring, normalisation mode and tie-breaking."""
import json
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .models import ScoringMode, Submission, Team, TeamStatus

# Tier weights exactly as specified in the brief.
TIER_POINTS = {1: 100, 2: 200, 3: 300, 4: 400, 5: 500}

CHALLENGES_PER_ROUND = {1: 3, 2: 3, 3: 4, 4: 4, 5: 1}

TIER_MAX = sum(TIER_POINTS[r] * CHALLENGES_PER_ROUND[r] for r in CHALLENGES_PER_ROUND)
NORMALIZED_MAX = 3500


def normalized_weight(round_number: int, mode: ScoringMode) -> int:
    """Proportionally scale the tier weight to the 3500-point ceiling.

    ratio = 3500 / 4200 = 0.8333333
    Documented rounding policy: round-half-up on each tier weight, which yields
    83 / 167 / 250 / 333 / 417 and an actual achievable maximum of 3499
    (a documented +1 rounding delta against the nominal 3500 ceiling).
    """
    if mode == ScoringMode.TIER:
        return TIER_POINTS[round_number]
    ratio = NORMALIZED_MAX / TIER_MAX
    return int(TIER_POINTS[round_number] * ratio + 0.5)


def max_possible(mode: ScoringMode) -> int:
    if mode == ScoringMode.TIER:
        return TIER_MAX
    return sum(normalized_weight(r, mode) * CHALLENGES_PER_ROUND[r] for r in CHALLENGES_PER_ROUND)


def scoring_summary(mode: ScoringMode) -> dict:
    return {
        "mode": mode.value,
        "max_possible": max_possible(mode),
        "nominal_ceiling": TIER_MAX if mode == ScoringMode.TIER else NORMALIZED_MAX,
        "weights": {str(r): normalized_weight(r, mode) for r in TIER_POINTS},
        "rounding_policy": (
            "Tier weights are used verbatim." if mode == ScoringMode.TIER else
            "Each tier weight is scaled by 3500/4200 and rounded half-up. "
            "The achievable total is 3499 (documented -1 rounding delta)."
        ),
    }


def recompute_points(sub: Submission, mode: ScoringMode, hint_penalty: int) -> int:
    if not sub.correct:
        return 0
    base = normalized_weight(sub.round_number, mode)
    return max(0, base - max(0, hint_penalty) * sub.hint_used)


def team_stats(db: Session, team: Team, mode: ScoringMode, hint_penalty: int) -> dict:
    subs = db.execute(
        select(Submission).where(Submission.team_id == team.id)
    ).scalars().all()
    solved = [s for s in subs if s.correct]
    total = sum(recompute_points(s, mode, hint_penalty) for s in solved)
    violations = 0
    from .models import Violation
    violations = db.execute(
        select(func.count(Violation.id)).where(
            Violation.team_id == team.id, Violation.forgiven.is_(False))
    ).scalar()
    last = max((s.at for s in solved), default=None)
    return {
        "solved": len(solved),
        "attempted": len(subs),
        "points": total,
        "violations": violations,
        "disqualified": team.status == TeamStatus.DISQUALIFIED,
        "last_solve_at": last.isoformat() if last else None,
    }


def leaderboard(db: Session, mode: ScoringMode, hint_penalty: int,
                frozen: bool = False) -> list[dict]:
    teams = db.execute(select(Team)).scalars().all()
    rows = []
    for t in teams:
        st = team_stats(db, t, mode, hint_penalty)
        rows.append({"team": t.name, "team_code": t.team_code, **st})
    rows.sort(key=lambda r: (
        -r["points"],
        r["last_solve_at"] or "9999",
        r["violations"],
        r["team"].lower(),
    ))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        if r["disqualified"]:
            r["status"] = "disqualified"
        elif r["violations"]:
            r["status"] = "flagged"
        else:
            r["status"] = "clean"
    return rows


def csv_report(rows: list[dict]) -> str:
    import csv, io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Rank", "Team", "Code", "Solved", "Attempted", "Points", "Violations", "Status"])
    for r in rows:
        w.writerow([r["rank"], r["team"], r["team_code"], r["solved"],
                    r["attempted"], r["points"], r["violations"], r["status"]])
    return buf.getvalue()