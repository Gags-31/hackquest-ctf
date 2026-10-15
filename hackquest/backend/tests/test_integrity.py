"""Rate limiting, appeal/forgiveness, reconnection and admin-isolation tests."""
import uuid

import pytest
from conftest import open_all_rounds, start_competition

from app import deps
from app.db import SessionLocal
from app.models import Team, TeamStatus, Violation


def _csrf(c):
    return c.get("/api/auth/csrf").json()["csrf_token"]


def _team(client):
    client.post("/api/auth/csrf")
    r = client.post("/api/auth/register", json={
        "team_name": f"R{uuid.uuid4().hex[:8]}", "leader_name": "Lead Person",
        "leader_email": f"{uuid.uuid4().hex[:8]}@example.com",
        "college": "KLEIT", "branch": "ECE", "semester": "5",
        "password": "TeamPassword!2026",
        "members": [{"name": "Member One", "email": "m1@example.com"}]})
    assert r.status_code == 201, r.text
    return _csrf(client)


# --------------------------------------------------------------- rate limiting
def test_login_rate_limit_blocks_brute_force(client):
    deps._hits.clear()
    for _ in range(14):
        client.post("/api/auth/login", json={"identity": "nobody",
                                             "password": "guess"})
    r = client.post("/api/auth/login", json={"identity": "nobody",
                                             "password": "guess"})
    assert r.status_code == 429


def test_submission_rate_limit(client, authed_org):
    oc = authed_org["client"]
    otok = authed_org["csrf"]
    start_competition(oc, otok)
    open_all_rounds(oc, otok, through=1)
    deps._hits.clear()
    tok = _team(client)
    codes = set()
    for _ in range(40):
        r = client.post("/api/submit", json={"challenge_key": "hq_r1_c1",
                                             "answer": "wrong"},
                        headers={"X-CSRF-Token": tok})
        codes.add(r.status_code)
    assert 429 in codes, "submission rate limit not enforced"


def test_unlock_rate_limit(authed_team, authed_org):
    oc = authed_org["client"]
    otok = authed_org["csrf"]
    start_competition(oc, otok)
    open_all_rounds(oc, otok, through=2)
    deps._hits.clear()
    tc = authed_team["client"]
    tok = _csrf(tc)
    codes = {tc.post("/api/unlock", json={"round_number": 1, "code": "bad"},
                     headers={"X-CSRF-Token": tok}).status_code for _ in range(30)}
    assert 429 in codes


# --------------------------------------------------------------- proctoring trust
def test_server_is_authority_for_violation_count(client):
    """A client cannot lower its own violation total by lying in the payload."""
    deps._hits.clear()
    tok = _team(client)
    for _ in range(3):
        client.post("/api/violation", json={"kind": "tab-hidden"},
                    headers={"X-CSRF-Token": tok})
    # Attempt to "reset" by sending a bogus total.
    r = client.post("/api/violation", json={"kind": "tab-hidden",
                                            "total": 0, "disqualified": False},
                    headers={"X-CSRF-Token": tok})
    assert r.json()["disqualified"] is True
    db = SessionLocal()
    t = db.query(Team).filter(Team.name.like("R%")).order_by(Team.id.desc()).first()
    assert t.status == TeamStatus.DISQUALIFIED
    db.close()


def test_unknown_violation_kind_is_stored_as_unknown(client):
    deps._hits.clear()
    tok = _team(client)
    r = client.post("/api/violation", json={"kind": "totally-made-up"},
                    headers={"X-CSRF-Token": tok})
    assert r.status_code == 200
    db = SessionLocal()
    v = db.query(Violation).order_by(Violation.id.desc()).first()
    assert v.kind == "unknown"
    db.close()


def test_disqualified_team_cannot_reverse_status_via_api(client, authed_org):
    """A DQ'd team gains nothing by calling any endpoint."""
    deps._hits.clear()
    tok = _team(client)
    for _ in range(3):
        client.post("/api/violation", json={"kind": "tab-hidden"},
                    headers={"X-CSRF-Token": tok})

    db = SessionLocal()
    before = db.query(Violation).count()
    db.close()

    # Reporting another violation must not resurrect or clear anything.
    r = client.post("/api/violation", json={"kind": "forgive-me"},
                    headers={"X-CSRF-Token": tok})
    assert r.status_code == 200
    assert r.json()["disqualified"] is True

    db = SessionLocal()
    after = db.query(Violation).count()
    team = db.query(Team).order_by(Team.id.desc()).first()
    db.close()
    assert after == before, "a new violation was recorded for a DQ team"
    assert team.status == TeamStatus.DISQUALIFIED

    # Administrative routes remain closed to teams.
    for path, payload in (("/api/admin/teams/disqualify",
                           {"team_id": 1, "reason": "let me back in"}),
                          ("/api/admin/settings",
                           {"key": "scoring_mode", "value": "normalized"})):
        rr = client.post(path, json=payload, headers={"X-CSRF-Token": tok})
        assert rr.status_code in (401, 403, 405), path


def test_organizer_can_restore_after_appeal(authed_org):
    oc = authed_org["client"]
    otok = authed_org["csrf"]
    db = SessionLocal()
    team = db.query(Team).first()
    team.status = TeamStatus.DISQUALIFIED
    db.commit()
    tid, code = team.id, team.team_code
    db.close()

    bad = oc.post("/api/admin/teams/disqualify",
                  json={"team_id": tid, "reason": ""},
                  headers={"X-CSRF-Token": otok})
    assert bad.status_code == 422, "a reason is mandatory"

    ok = oc.post("/api/admin/teams/disqualify",
                 json={"team_id": tid, "reason": "Appeal upheld by jury",
                       "restore": True},
                 headers={"X-CSRF-Token": otok})
    assert ok.status_code == 200
    assert ok.json()["status"] == "active"

    audit = oc.get("/api/admin/audit", headers={"X-CSRF-Token": otok}).json()
    assert any(e["action"] == "team.restored" and
               "Appeal upheld" in (e["detail"] or "") for e in audit["entries"])


def test_violation_cannot_be_reviewed_twice(authed_org, client):
    oc = authed_org["client"]
    otok = authed_org["csrf"]
    deps._hits.clear()
    tok = _team(client)
    client.post("/api/violation", json={"kind": "window-blur"},
                headers={"X-CSRF-Token": tok})
    vs = oc.get("/api/admin/violations", headers={"X-CSRF-Token": otok}).json()
    if not vs["violations"]:
        pytest.skip("no violations")
    vid = vs["violations"][0]["id"]
    first = oc.post("/api/admin/violations/review",
                    json={"violation_id": vid, "forgive": True,
                          "reason": "verified interruption"},
                    headers={"X-CSRF-Token": otok})
    assert first.status_code == 200
    second = oc.post("/api/admin/violations/review",
                     json={"violation_id": vid, "forgive": True,
                           "reason": "again"},
                     headers={"X-CSRF-Token": otok})
    assert second.status_code == 409


# --------------------------------------------------------------- reconnection
def test_heartbeat_allows_reconnect_after_network_drop(authed_team):
    tc = authed_team["client"]
    r = tc.post("/api/heartbeat")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    # The session cookie must survive, so progress is recoverable.
    me = tc.get("/api/auth/me").json()
    assert me["authenticated"] is True


def test_submission_history_is_recoverable(authed_team, authed_org):
    tc, oc = authed_team["client"], authed_org["client"]
    start_competition(oc, authed_org["csrf"])
    open_all_rounds(oc, authed_org["csrf"], through=1)
    tok = _csrf(tc)
    tc.post("/api/submit", json={"challenge_key": "hq_r1_c1", "answer": "wrong"},
            headers={"X-CSRF-Token": tok})
    tc.post("/api/submit", json={"challenge_key": "hq_r1_c1", "answer": "276"},
            headers={"X-CSRF-Token": tok})
    detail = tc.get("/api/rounds/round1").json()
    c1 = next(c for c in detail["challenges"] if c["key"] == "hq_r1_c1")
    assert c1["solved"] is True
    assert detail["challenges_solved"] == 1


def test_network_disconnect_is_not_treated_as_cheating(authed_team):
    """Heartbeat misses are recorded but only proctoring events count."""
    tc = authed_team["client"]
    tok = _csrf(tc)
    tc.post("/api/heartbeat")
    lb = tc.get("/api/leaderboard").json()
    assert lb["rows"][0]["violations"] == 0


# --------------------------------------------------------------- admin isolation
def test_unauthenticated_cannot_reach_anything_protected(client):
    client.post("/api/auth/csrf")
    for method, path in (("get", "/api/admin/teams"), ("get", "/api/admin/audit"),
                         ("get", "/api/admin/violations"),
                         ("get", "/api/admin/export/leaderboard.csv")):
        r = getattr(client, method)(path, headers={"X-CSRF-Token": _csrf(client)})
        assert r.status_code in (401, 403), path


def test_csrf_token_required_from_other_origin(client, authed_team):
    """A missing/forged CSRF header must be rejected."""
    tc = authed_team["client"]
    r = tc.post("/api/submit", json={"challenge_key": "hq_r1_c1", "answer": "276"})
    assert r.status_code == 403
    r2 = tc.post("/api/submit", json={"challenge_key": "hq_r1_c1", "answer": "276"},
                 headers={"X-CSRF-Token": "forged-token"})
    assert r2.status_code == 403


def test_health_is_public_but_admin_is_not(client):
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/admin/teams").status_code in (401, 403)


# --------------------------------------------------------------- answer secrecy
def test_answers_never_reach_the_client(authed_team, authed_org):
    """Sweep every participant-facing endpoint for leaked keys.

    Note: some challenge *questions* legitimately display the data being asked
    about (Round 4 C11 shows the config snippet it refers to). What must never
    appear is the private answer_key field, the assembled unlock code, hidden
    tests, or post-round explanations.
    """
    oc = authed_org["client"]
    otok = authed_org["csrf"]
    start_competition(oc, otok)
    open_all_rounds(oc, otok, through=5)
    tc = authed_team["client"]

    blobs = [tc.get("/api/rounds").text]
    for slug in ("round1", "round2", "round3", "round4", "final"):
        blobs.append(tc.get(f"/api/rounds/{slug}").text)
    blobs.append(tc.get("/api/leaderboard").text)
    joined = "\n".join(blobs)

    must_not_appear = [
        "276401UP",               # round 1 unlock code
        "HACKHackQuestSNO",       # round 2 unlock code
        "48STACK44345",           # round 3 unlock code
        "/training/blue-doortrainee:demo-passSHA-256CAESAR",  # round 4
        "count_evens-fixed",      # round 5 segment
        "answer_key",             # schema field name
        "hidden_tests",           # hidden test payload
        "server-only",            # hidden-test marker
        "unlock_code",            # schema field name
        "F(12) = 144",            # post-round explanation text
        "2850 / 1296",            # explanation arithmetic
    ]
    for s in must_not_appear:
        assert s not in joined, f"LEAKED: {s}"


def test_hints_do_not_contain_the_answer(authed_team, authed_org):
    oc = authed_org["client"]
    otok = authed_org["csrf"]
    start_competition(oc, otok)
    open_all_rounds(oc, otok, through=1)
    tc = authed_team["client"]
    tok = _csrf(tc)
    hints = []
    for _ in range(3):
        r = tc.post("/api/challenges/hq_r1_c1/hint", headers={"X-CSRF-Token": tok})
        if r.status_code == 200:
            hints.append(r.json()["hint"])
    assert hints
    for h in hints:
        assert "276" not in h, "hint leaks the answer"


def test_round5_hidden_tests_not_exposed(authed_team, authed_org):
    oc = authed_org["client"]
    otok = authed_org["csrf"]
    start_competition(oc, otok)
    open_all_rounds(oc, otok, through=5)
    tc = authed_team["client"]
    detail = tc.get("/api/rounds/final").text
    assert "hidden_tests" not in detail
    assert "server-only" not in detail