"""Test harness: isolated SQLite database and HTTP client."""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_tmp = tempfile.mkdtemp(prefix="hqctf2026-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp) / 'test.db'}"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["ENVIRONMENT"] = "testing"
os.environ["ORG1_PASSWORD"] = "TestOrgOne!2026"
os.environ["ORG2_PASSWORD"] = "TestOrgTwo!2026"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import run as seed_run  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def prepared_db():
    init_db()
    seed_run(refresh=True)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _organiser(username, password):
    with TestClient(app) as c:
        r = c.post("/api/auth/login", json={
            "username": username, "password": password})
        assert r.status_code == 200, r.text
        yield c
        c.post("/api/auth/logout")


@pytest.fixture
def org_client():
    yield from _organiser("pragyan_lead", "TestOrgOne!2026")


@pytest.fixture
def coorg_client():
    yield from _organiser("ieee_lead", "TestOrgTwo!2026")


def register(client, name, members=2, email_prefix=None):
    prefix = email_prefix or name.lower().replace(" ", "")
    payload = {
        "team_name": name, "college": "KLEIT", "department": "CSE",
        "semester": "4", "leader_name": f"{name} Leader",
        "leader_email": f"{prefix}leader@example.com",
        "password": "TeamPass!2026",
        "members": [
            {"name": f"{name} Member {i}", "email": f"{prefix}{i}@example.com",
             "mobile": f"987654321{i}"} for i in range(1, members + 1)
        ],
    }
    return client.post("/api/auth/register", json=payload)


def csrf(client):
    return client.get("/api/auth/csrf").json()["csrf"]


def login(client, name):
    return client.post("/api/auth/login", json={"username": name, "password": "TeamPass!2026"})


def headers(client):
    return {"x-csrf-token": csrf(client)}
