"""Shared pytest fixtures. Uses an isolated SQLite database per test session."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_TMP_DB = Path(tempfile.gettempdir()) / "hackquest_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["ENVIRONMENT"] = "test"
os.environ["PROCTOR_VIOLATION_LIMIT"] = "3"
os.environ["HINT_PENALTY"] = "0"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine, init_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.models import (AppSetting, Organizer, Round, RoundState,  # noqa: E402
                         ScoringMode)
from app.seed import run as seed_run  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _database():
    if _TMP_DB.exists():
        _TMP_DB.unlink()
    init_db()
    seed_run()
    yield
    # Dispose pooled connections before removing the file on Windows.
    engine.dispose()
    if _TMP_DB.exists():
        try:
            _TMP_DB.unlink()
        except PermissionError:
            pass


@pytest.fixture(autouse=True)
def _reset_event_state(_database):
    """Reset shared, event-wide state before each test.

    The database is session-scoped and shared, so round visibility and the
    competition timer would otherwise leak from one test into the next.
    """
    db = SessionLocal()
    try:
        for rd in db.query(Round).all():
            rd.state = RoundState.LOCKED
        for key, val in (("competition_state", "pending"),
                         ("results_frozen", "0"),
                         ("results_published", "0"),
                         ("hint_penalty", "0"),
                         ("scoring_mode", ScoringMode.TIER.value)):
            row = db.query(AppSetting).filter_by(key=key).first()
            if not row:
                db.add(AppSetting(key=key, value=val))
            else:
                row.value = val
        db.commit()
    finally:
        db.close()

    # Rate limiting is exercised by dedicated tests; clear it so ordinary
    # tests are not throttled by earlier registrations from the same IP.
    from app import deps
    deps._hits.clear()

    yield


@pytest.fixture
def client(_database):
    """Function-scoped so cookies never leak between tests.

    The lifespan context manager is deliberately not used: creating and tearing
    down a lifespan per test destabilises Starlette's task groups. The schema and
    seed data are created once by the session-scoped `_database` fixture.
    """
    return TestClient(fastapi_app)


@pytest.fixture
def organizer(client):
    db = SessionLocal()
    if not db.query(Organizer).filter_by(username="lead").first():
        db.add(Organizer(username="lead", email="lead@kleit.ac.in",
                         full_name="Lead Organizer", role="admin",
                         password_hash=hash_password("LeadOrganizer!2026"),
                         must_change_password=False))
    if not db.query(Organizer).filter_by(username="second").first():
        db.add(Organizer(username="second", email="second@kleit.ac.in",
                         full_name="Second Organizer", role="moderator",
                         password_hash=hash_password("SecondOrganizer!2026"),
                         must_change_password=False))
    db.commit()
    db.close()
    return {"username": "lead", "password": "LeadOrganizer!2026"}


@pytest.fixture
def mod(org_client):
    return {"username": "second", "password": "SecondOrganizer!2026"}


def _csrf(client, jar):
    r = client.get("/api/auth/csrf")
    return r.json()["csrf_token"]


@pytest.fixture
def team_client(client):
    """Registers a team and returns (client, cookies, csrf, team payload)."""
    import uuid
    name = f"Team{uuid.uuid4().hex[:8]}"
    jar = client.cookies
    client.post("/api/auth/csrf")
    csrf = client.cookies.get("hq_csrf")

    def register(team_name=None, email=None, members=1):
        nm = team_name or f"Team{uuid.uuid4().hex[:8]}"
        em = email or f"{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "team_name": nm,
            "leader_name": "Leader Person",
            "leader_email": em,
            "college": "KLEIT",
            "branch": "ECE",
            "semester": "5",
            "password": "TeamPassword!2026",
            "members": [{"name": f"Member {i}",
                         "email": f"m{i}.{uuid.uuid4().hex[:6]}@example.com",
                         "branch": "ECE", "semester": "5", "college": "KLEIT"}
                        for i in range(members)],
        }
        return client.post("/api/auth/register", json=payload)

    return {"client": client, "csrf": csrf, "register": register}


@pytest.fixture
def authed_team(team_client):
    r = team_client["register"](members=2)
    assert r.status_code == 201, r.text
    team_client["csrf"] = r.cookies.get("hq_csrf") or team_client["csrf"]
    return team_client


@pytest.fixture
def org_client(_database):
    """A second, independent browser session for organizer actions.

    A single browser cannot be both a team and an organizer, so organizer
    calls must use a separate cookie jar from participant calls.
    """
    return TestClient(fastapi_app)


@pytest.fixture
def authed_org(org_client, organizer):
    org_client.post("/api/auth/csrf")
    r = org_client.post("/api/auth/login",
                        json={"identity": organizer["username"],
                              "password": organizer["password"]})
    assert r.status_code == 200, r.text
    csrf = r.cookies.get("hq_csrf") or org_client.cookies.get("hq_csrf")
    return {"client": org_client, "csrf": csrf}


def open_all_rounds(client, csrf, through=5):
    for n in range(1, through + 1):
        client.post("/api/admin/rounds",
                    json={"number": n, "state": "open"},
                    headers={"X-CSRF-Token": csrf})


def start_competition(client, csrf):
    client.post("/api/admin/competition?state=running",
                headers={"X-CSRF-Token": csrf})