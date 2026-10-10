"""Test generator — emits a pytest suite for the generated backend.

Tests trace back to requirements: auth flows, per-entity CRUD, RBAC and
validation, executed by the Testing Agent in the validation pipeline.
"""
from __future__ import annotations

from typing import Any

from ..core.nlp import to_snake
from .common import create_payload, fk_fields


def render_conftest() -> str:
    return '''"""Test fixtures: isolated SQLite database + authenticated client."""
import os
import tempfile

_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_fd)
os.environ["DATABASE_URL"] = "sqlite:///" + _db_path
os.environ["AUTH_RATE_LIMIT"] = "100000"  # disable throttling during the test suite

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestClient(app)


def _register_and_login(client: TestClient, email: str, password: str,
                        full_name: str = "Test User") -> dict:
    resp = client.post("/api/auth/register", json={
        "email": email, "password": password, "full_name": full_name})
    assert resp.status_code == 201, resp.text
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": "Bearer " + resp.json()["access_token"]}


@pytest.fixture()
def auth_headers(client):
    return _register_and_login(client, "tester@example.com", "Str0ngPass!")


@pytest.fixture()
def other_headers(client):
    return _register_and_login(client, "other@example.com", "Str0ngPass!")
'''


def render_test_auth() -> str:
    return '''"""Requirement traceability: User Registration, User Login, RBAC."""


def test_register_and_login(client):
    resp = client.post("/api/auth/register", json={
        "email": "alice@example.com", "password": "Str0ngPass!", "full_name": "Alice"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["user"]["email"] == "alice@example.com"
    assert "password" not in body["user"] and "password_hash" not in body["user"]


def test_register_rejects_weak_password(client):
    resp = client.post("/api/auth/register", json={
        "email": "bob@example.com", "password": "short", "full_name": "Bob"})
    assert resp.status_code == 422


def test_register_rejects_invalid_email(client):
    resp = client.post("/api/auth/register", json={
        "email": "not-an-email", "password": "Str0ngPass!", "full_name": "Bob"})
    assert resp.status_code == 422


def test_duplicate_email_conflict(client):
    payload = {"email": "carol@example.com", "password": "Str0ngPass!", "full_name": "Carol"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409


def test_login_success_and_wrong_password(client):
    client.post("/api/auth/register", json={
        "email": "dave@example.com", "password": "Str0ngPass!", "full_name": "Dave"})
    ok = client.post("/api/auth/login", json={"email": "dave@example.com",
                                              "password": "Str0ngPass!"})
    assert ok.status_code == 200 and ok.json()["access_token"]
    bad = client.post("/api/auth/login", json={"email": "dave@example.com",
                                               "password": "Wr0ngPass!"})
    assert bad.status_code == 401


def test_me_requires_and_accepts_token(client, auth_headers):
    assert client.get("/api/users/me").status_code == 401
    resp = client.get("/api/users/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "tester@example.com"


def test_admin_endpoint_forbidden_for_regular_user(client, auth_headers):
    assert client.get("/api/users", headers=auth_headers).status_code == 403
'''


def render_test_entity(ent: dict[str, Any], entities: list[dict[str, Any]]) -> str:
    name, table = ent["name"], ent["table"]
    resource = table.replace("_", "-")
    by_name = {e["name"]: e for e in entities}

    # Direct parents that must exist before this entity can be created.
    parents: list[str] = []
    for field in fk_fields(ent):
        ref = field.get("ref")
        if ref and ref != "User" and ref in by_name and ref not in parents:
            parents.append(ref)

    setup_lines: list[str] = []
    for ref in parents:
        parent = by_name[ref]
        parent_resource = parent["table"].replace("_", "-")
        parent_payload = create_payload(parent, 1, {})
        setup_lines.append(
            f"    resp = client.post(\"/api/{parent_resource}\", json={parent_payload!r}, "
            f"headers=headers)")
        setup_lines.append("    assert resp.status_code == 201, resp.text")
        setup_lines.append(f"    fk_ids[\"{to_snake(ref)}_id\"] = resp.json()[\"id\"]")
    setup = "\n".join(setup_lines) if setup_lines else "    pass"

    base_payload = create_payload(ent, 1, {})
    fk_names = [to_snake(f["ref"]) + "_id" for f in fk_fields(ent)
                if f.get("ref") and f["ref"] != "User"]

    update_field = next((f for f in ent["fields"]
                         if f["name"] not in ("id", "created_at")
                         and f["type"] in ("str", "text")), None)
    if update_field:
        update_body = {update_field["name"]: "Updated value"}
    else:
        num_field = next((f for f in ent["fields"]
                          if f["name"] not in ("id", "created_at")
                          and f["type"] in ("int", "float")), None)
        update_body = {num_field["name"]: 123} if num_field else {}

    return f'''"""Requirement traceability: {name} management (CRUD + auth + validation)."""
RESOURCE = "/api/{resource}"


def _fk_ids(client, headers):
    fk_ids = {{}}
{setup}
    return fk_ids


def _create(client, headers):
    fk_ids = _fk_ids(client, headers)
    payload = dict({base_payload!r})
    for key, value in fk_ids.items():
        if key in payload or key in {fk_names!r}:
            payload[key] = value
    resp = client.post(RESOURCE, json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_list_get(client, auth_headers):
    created = _create(client, auth_headers)
    assert created["id"] >= 1

    resp = client.get(RESOURCE, headers=auth_headers)
    assert resp.status_code == 200
    assert any(row["id"] == created["id"] for row in resp.json())

    resp = client.get(RESOURCE + "/" + str(created["id"]), headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_update_and_delete(client, auth_headers):
    created = _create(client, auth_headers)
    resp = client.put(RESOURCE + "/" + str(created["id"]), json={update_body!r},
                      headers=auth_headers)
    assert resp.status_code == 200, resp.text

    resp = client.delete(RESOURCE + "/" + str(created["id"]), headers=auth_headers)
    assert resp.status_code == 204
    assert client.get(RESOURCE + "/" + str(created["id"]),
                      headers=auth_headers).status_code == 404


def test_requires_authentication(client):
    assert client.get(RESOURCE).status_code == 401
    assert client.post(RESOURCE, json={{}}).status_code == 401


def test_not_found(client, auth_headers):
    assert client.get(RESOURCE + "/999999", headers=auth_headers).status_code == 404
'''


def render_test_init() -> str:
    return ""
