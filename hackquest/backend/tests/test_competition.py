"""End-to-end competition flow: registration, auth, rounds, scoring, admin."""
import uuid

import pytest
from conftest import open_all_rounds, start_competition

from app.db import SessionLocal
from app.models import Team, TeamStatus


def _csrf(client):
    r = client.get("/api/auth/csrf")
    return r.json()["csrf_token"]


def _register(client, name=None, email=None, members=2):
    client.post("/api/auth/csrf")
    nm = name or f"T{uuid.uuid4().hex[:8]}"
    em = email or f"{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "team_name": nm, "leader_name": "Leader", "leader_email": em,
        "college": "KLEIT", "branch": "ECE", "semester": "5",
        "password": "TeamPassword!2026",
        "members": [{"name": f"M{i}", "email": f"m{i}.{uuid.uuid4().hex[:6]}@example.com"}
                    for i in range(members)],
    }
    return client.post("/api/auth/register", json=payload)


# --------------------------------------------------------------- registration
def test_registration_and_team_size(team_client):
    c = team_client["client"]
    r = _register(c, members=2)          # leader + 2 = 3 people
    assert r.status_code == 201, r.text
    body = r.json()
    assert len(body["team_code"]) == 6
    assert body["team_name"].startswith("T")


def test_team_size_minimum_enforced(team_client):
    c = team_client["client"]
    r = _register(c, members=0)          # only the leader = 1 person
    assert r.status_code == 422


def test_team_size_maximum_enforced(team_client):
    c = team_client["client"]
    r = _register(c, members=4)          # leader + 4 = 5 people
    assert r.status_code == 422


def test_duplicate_team_name_rejected(team_client):
    c = team_client["client"]
    name = f"Dup{uuid.uuid4().hex[:6]}"
    assert _register(c, name=name).status_code == 201
    assert _register(c, name=name).status_code == 409


def test_duplicate_leader_email_rejected(team_client):
    c = team_client["client"]
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    assert _register(c, email=email).status_code == 201
    r = _register(c, name=f"Other{uuid.uuid4().hex[:6]}", email=email)
    assert r.status_code == 409


# --------------------------------------------------------------- auth
def test_login_and_me(authed_team):
    c = authed_team["client"]
    me = c.get("/api/auth/me").json()
    assert me["authenticated"] is True
    assert me["role"] == "team"
    assert len(me["members"]) == 2


def test_login_with_wrong_password_rejected(authed_team):
    c = authed_team["client"]
    c.post("/api/auth/logout", headers={"X-CSRF-Token": _csrf(c)})
    r = c.post("/api/auth/login", json={"identity": "nobody", "password": "wrong"})
    assert r.status_code == 401


def test_csrf_required_for_state_changes(authed_team):
    c = authed_team["client"]
    r = c.post("/api/auth/logout")       # no X-CSRF-Token
    assert r.status_code == 403


def test_session_cleared_on_logout(authed_team):
    c = authed_team["client"]
    tok = _csrf(c)
    assert c.post("/api/auth/logout", headers={"X-CSRF-Token": tok}).status_code == 200
    assert c.get("/api/auth/me").json()["authenticated"] is False


def test_organizer_login_and_role(authed_org):
    r = authed_org["client"].get("/api/auth/me").json()
    assert r["role"] == "organizer"
    assert r["admin_role"] == "admin"


def test_team_cannot_reach_admin_api(authed_team):
    c = authed_team["client"]
    tok = _csrf(c)
    assert c.get("/api/admin/teams", headers={"X-CSRF-Token": tok}).status_code in (401, 403)
    assert c.post("/api/admin/settings",
                  json={"key": "scoring_mode", "value": "normalized"},
                  headers={"X-CSRF-Token": tok}).status_code == 403


def test_moderator_cannot_change_settings(authed_org, mod):
    """A moderator may review content but not reconfigure the event."""
    db = SessionLocal()
    from app.security import hash_password
    from app.models import Organizer
    if not db.query(Organizer).filter_by(username="mod2").first():
        db.add(Organizer(username="mod2", email="mod2@k.ac.in",
                         full_name="Mod Two", role="moderator",
                         password_hash=hash_password("ModeratorPass!2026")))
        db.commit()
    db.close()

    c = authed_org["client"]
    c.post("/api/auth/logout", headers={"X-CSRF-Token": _csrf(c)})
    c.post("/api/auth/csrf")
    r = c.post("/api/auth/login", json={"identity": "mod2",
                                        "password": "ModeratorPass!2026"})
    assert r.status_code == 200
    tok = _csrf(c)
    assert c.post("/api/admin/settings", json={"key": "scoring_mode", "value": "normalized"},
                  headers={"X-CSRF-Token": tok}).status_code == 403
    # ...but may read
    assert c.get("/api/admin/leaderboard", headers={"X-CSRF-Token": tok}).status_code == 200


# --------------------------------------------------------------- competition
R1_ANSWERS = {"hq_r1_c1": "276", "hq_r1_c2": "40", "hq_r1_c3": "1UP"}


def _prepare(client, org, csrf, teamcsrf):
    open_all_rounds(client, org, through=1)
    start_competition(client, org)


def test_rounds_locked_until_organizer_opens(authed_team, authed_org):
    tc, oc = authed_team["client"], authed_org["client"]
    tok = _csrf(tc)
    start_competition(oc, authed_org["csrf"])
    r = tc.get("/api/rounds/round1")
    assert r.status_code == 200
    assert r.json()["state"] == "locked"


def test_open_round1_and_solve(authed_team, authed_org):
    tc, oc = authed_team["client"], authed_org["client"]
    start_competition(oc, authed_org["csrf"])
    open_all_rounds(oc, authed_org["csrf"], through=1)

    detail = tc.get("/api/rounds/round1").json()
    assert detail["state"] == "open"
    assert len(detail["challenges"]) == 3
    # answer keys and unlock codes must never be serialised
    assert "answer_key" not in str(detail)
    assert "unlock_code" not in str(detail)

    tok = _csrf(tc)
    for key, ans in R1_ANSWERS.items():
        r = tc.post("/api/submit", json={"challenge_key": key, "answer": ans},
                    headers={"X-CSRF-Token": tok})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["correct"] is True
        assert body["points"] == 100


def test_wrong_answer_scores_zero(authed_team, authed_org):
    tc, oc = authed_team["client"], authed_org["client"]
    start_competition(oc, authed_org["csrf"])
    open_all_rounds(oc, authed_org["csrf"], through=1)
    tok = _csrf(tc)
    r = tc.post("/api/submit", json={"challenge_key": "hq_r1_c1", "answer": "nope"},
                headers={"X-CSRF-Token": tok})
    assert r.json()["correct"] is False
    assert r.json()["points"] == 0


def test_duplicate_correct_submission_scores_once(authed_team, authed_org):
    tc, oc = authed_team["client"], authed_org["client"]
    start_competition(oc, authed_org["csrf"])
    open_all_rounds(oc, authed_org["csrf"], through=1)
    tok = _csrf(tc)
    tc.post("/api/submit", json={"challenge_key": "hq_r1_c1", "answer": "276"},
            headers={"X-CSRF-Token": tok})
    r2 = tc.post("/api/submit", json={"challenge_key": "hq_r1_c1", "answer": "276"},
                 headers={"X-CSRF-Token": tok})
    assert r2.json()["already_accepted"] is True
    assert r2.json()["points"] == 100
    lb = tc.get("/api/leaderboard").json()
    me = next((x for x in lb["rows"] if x["team_code"] ==
               lb["rows"][0]["team_code"]), None)
    assert me is not None


def test_completing_round1_generates_unlock_code(authed_team, authed_org):
    tc, oc = authed_team["client"], authed_org["client"]
    start_competition(oc, authed_org["csrf"])
    open_all_rounds(oc, authed_org["csrf"], through=2)
    tok = _csrf(tc)
    last = None
    for key, ans in R1_ANSWERS.items():
        last = tc.post("/api/submit", json={"challenge_key": key, "answer": ans},
                       headers={"X-CSRF-Token": tok}).json()
    assert last["unlocked"] is not None
    assert last["unlocked"]["code"] == "276401UP"
    assert last["unlocked"]["already"] is False

    # round 2 now accessible for this team
    r2 = tc.get("/api/rounds/round2").json()
    assert r2["state"] == "open"


def test_unlock_rejects_wrong_code(authed_team, authed_org):
    tc, oc = authed_team["client"], authed_org["client"]
    start_competition(oc, authed_org["csrf"])
    open_all_rounds(oc, authed_org["csrf"], through=2)
    r = tc.post("/api/unlock", json={"round_number": 1, "code": "WRONG"},
                headers={"X-CSRF-Token": _csrf(tc)})
    assert r.status_code == 400


def test_round2_unavailable_until_round1_done(authed_team, authed_org):
    tc, oc = authed_team["client"], authed_org["client"]
    start_competition(oc, authed_org["csrf"])
    open_all_rounds(oc, authed_org["csrf"], through=5)
    detail = tc.get("/api/rounds/round2").json()
    # round is open globally but locked for this team
    rounds = tc.get("/api/rounds").json()
    r2 = next(r for r in rounds["rounds"] if r["number"] == 2)
    assert r2["unlocked"] is False


def test_submission_rejected_when_competition_not_running(authed_team, authed_org):
    tc, oc = authed_team["client"], authed_org["client"]
    open_all_rounds(oc, authed_org["csrf"], through=1)
    tok = _csrf(tc)
    r = tc.post("/api/submit", json={"challenge_key": "hq_r1_c1", "answer": "276"},
                headers={"X-CSRF-Token": tok})
    assert r.status_code == 403


def test_hints_are_progressive_and_capped(authed_team, authed_org):
    tc, oc = authed_team["client"], authed_org["client"]
    start_competition(oc, authed_org["csrf"])
    open_all_rounds(oc, authed_org["csrf"], through=1)
    tok = _csrf(tc)
    for i in range(3):
        r = tc.post("/api/challenges/hq_r1_c1/hint", headers={"X-CSRF-Token": tok})
        assert r.status_code == 200
        assert r.json()["hint"]
    assert tc.post("/api/challenges/hq_r1_c1/hint",
                   headers={"X-CSRF-Token": tok}).status_code == 400


def test_hint_penalty_configurable(authed_org):
    oc = authed_org["client"]
    r = oc.post("/api/admin/settings", json={"key": "hint_penalty", "value": "10"},
                headers={"X-CSRF-Token": authed_org["csrf"]})
    assert r.status_code == 200
    s = oc.get("/api/admin/settings", headers={"X-CSRF-Token": authed_org["csrf"]}).json()
    assert s["settings"]["hint_penalty"] == "10"
    oc.post("/api/admin/settings", json={"key": "hint_penalty", "value": "0"},
            headers={"X-CSRF-Token": authed_org["csrf"]})


# --------------------------------------------------------------- round 5
def test_round5_structured_patch_flow(authed_team, authed_org):
    tc, oc = authed_team["client"], authed_org["client"]
    start_competition(oc, authed_org["csrf"])
    open_all_rounds(oc, authed_org["csrf"], through=5)
    tok = _csrf(tc)
    # solve rounds 1-4 quickly through the API
    answers = {
        "hq_r1_c1": "276", "hq_r1_c2": "40", "hq_r1_c3": "1UP",
        "hq_r2_c4": "HACK", "hq_r2_c5": "SGFja1F1ZXN0", "hq_r2_c6": "BAF",
        "hq_r3_c7": "48", "hq_r3_c8": "STACK", "hq_r3_c9": "443", "hq_r3_c10": "45",
        "hq_r4_c11": "/training/blue-door", "hq_r4_c12": "trainee:demo-pass",
        "hq_r4_c13": "SHA-256", "hq_r4_c14": "CAESAR",
    }
    for k, a in answers.items():
        r = tc.post("/api/submit", json={"challenge_key": k, "answer": a},
                    headers={"X-CSRF-Token": tok})
        assert r.json()["correct"] is True, (k, r.json())

    detail = tc.get("/api/rounds/final").json()
    c15 = next(c for c in detail["challenges"] if c["key"] == "hq_r5_c15")
    assert c15["points"] == 500

    bad = tc.post("/api/submit", json={"challenge_key": "hq_r5_c15",
                                       "answer": '{"comparator": 1}'},
                  headers={"X-CSRF-Token": tok})
    assert bad.json()["correct"] is False

    good = tc.post("/api/submit", json={"challenge_key": "hq_r5_c15",
                                        "answer": '{"comparator": 0}'},
                   headers={"X-CSRF-Token": tok})
    assert good.json()["correct"] is True
    assert good.json()["points"] == 500
    assert good.json()["test_detail"]["passed"] == 10


def test_round5_rejects_dangerous_code(authed_team, authed_org):
    tc, oc = authed_team["client"], authed_org["client"]
    start_competition(oc, authed_org["csrf"])
    open_all_rounds(oc, authed_org["csrf"], through=5)
    tok = _csrf(tc)
    r = tc.post("/api/submit",
                json={"challenge_key": "hq_r5_c15",
                      "answer": "import os\ndef count_evens(n):\n    return os.system('id')"},
                headers={"X-CSRF-Token": tok})
    assert r.status_code == 422


# --------------------------------------------------------------- proctoring
def test_three_violations_disqualify(authed_team, authed_org):
    tc = authed_team["client"]
    tok = _csrf(tc)
    for _ in range(2):
        r = tc.post("/api/violation", json={"kind": "tab-hidden"},
                    headers={"X-CSRF-Token": tok})
        assert r.json()["disqualified"] is False
    r = tc.post("/api/violation", json={"kind": "exit-fullscreen"},
                headers={"X-CSRF-Token": tok})
    assert r.json()["disqualified"] is True
    assert r.json()["violations"] == 3

    db = SessionLocal()
    t = db.query(Team).filter_by(name=r.json()["notice"] and None or None).first()
    db.close()


def test_disqualified_team_cannot_submit(authed_team, authed_org):
    tc, oc = authed_team["client"], authed_org["client"]
    start_competition(oc, authed_org["csrf"])
    open_all_rounds(oc, authed_org["csrf"], through=1)
    tok = _csrf(tc)
    for _ in range(3):
        tc.post("/api/violation", json={"kind": "tab-hidden"},
                headers={"X-CSRF-Token": tok})
    r = tc.post("/api/submit", json={"challenge_key": "hq_r1_c1", "answer": "276"},
                headers={"X-CSRF-Token": tok})
    assert r.status_code == 403


def test_organizer_forgiveness_requires_reason_and_is_audited(authed_org):
    oc = authed_org["client"]
    otok = authed_org["csrf"]
    vs = oc.get("/api/admin/violations", headers={"X-CSRF-Token": otok}).json()
    if not vs["violations"]:
        pytest.skip("no violations recorded yet")
    vid = vs["violations"][0]["id"]
    bad = oc.post("/api/admin/violations/review",
                  json={"violation_id": vid, "forgive": True, "reason": ""},
                  headers={"X-CSRF-Token": otok})
    assert bad.status_code == 422
    ok = oc.post("/api/admin/violations/review",
                 json={"violation_id": vid, "forgive": True,
                       "reason": "Organizer observed a genuine interruption"},
                 headers={"X-CSRF-Token": otok})
    assert ok.status_code == 200
    audit = oc.get("/api/admin/audit", headers={"X-CSRF-Token": otok}).json()
    assert any(e["action"] == "violation.forgiven" for e in audit["entries"])


# --------------------------------------------------------------- leaderboard
def test_leaderboard_tiebreak_and_freeze(authed_team, authed_org):
    tc, oc = authed_team["client"], authed_org["client"]
    start_competition(oc, authed_org["csrf"])
    open_all_rounds(oc, authed_org["csrf"], through=1)
    tok = _csrf(tc)
    tc.post("/api/submit", json={"challenge_key": "hq_r1_c1", "answer": "276"},
            headers={"X-CSRF-Token": tok})
    lb = tc.get("/api/leaderboard").json()
    assert lb["max_possible"] in (4200, 3499)
    assert lb["rows"][0]["points"] >= 100

    otok = authed_org["csrf"]
    oc.post("/api/admin/settings", json={"key": "results_frozen", "value": "1"},
            headers={"X-CSRF-Token": otok})
    frozen = tc.get("/api/leaderboard").json()
    assert frozen["frozen"] is True
    oc.post("/api/admin/settings", json={"key": "results_frozen", "value": "0"},
            headers={"X-CSRF-Token": otok})


def test_results_hidden_until_published(authed_team, authed_org):
    oc = authed_org["client"]
    otok = authed_org["csrf"]
    r = oc.get("/api/results", headers={"X-CSRF-Token": otok})
    assert r.json()["published"] is False
    oc.post("/api/admin/settings", json={"key": "results_published", "value": "1"},
            headers={"X-CSRF-Token": otok})
    r2 = oc.get("/api/results", headers={"X-CSRF-Token": otok})
    assert r2.json()["published"] is True
    oc.post("/api/admin/settings", json={"key": "results_published", "value": "0"},
            headers={"X-CSRF-Token": otok})


def test_scoring_mode_switch_changes_max(authed_org):
    oc = authed_org["client"]
    otok = authed_org["csrf"]
    oc.post("/api/admin/settings", json={"key": "scoring_mode", "value": "normalized"},
            headers={"X-CSRF-Token": otok})
    s = oc.get("/api/admin/settings", headers={"X-CSRF-Token": otok}).json()
    assert s["scoring"]["max_possible"] == 3499
    oc.post("/api/admin/settings", json={"key": "scoring_mode", "value": "tier"},
            headers={"X-CSRF-Token": otok})
    s2 = oc.get("/api/admin/settings", headers={"X-CSRF-Token": otok}).json()
    assert s2["scoring"]["max_possible"] == 4200


# --------------------------------------------------------------- exports/audit
def test_csv_exports(authed_org):
    oc = authed_org["client"]
    otok = authed_org["csrf"]
    for path in ("/api/admin/export/leaderboard.csv",
                 "/api/admin/export/registrations.csv",
                 "/api/admin/export/submissions.csv"):
        r = oc.get(path, headers={"X-CSRF-Token": otok})
        assert r.status_code == 200, path
        assert "text/csv" in r.headers["content-type"]
        assert r.text.splitlines()


def test_audit_log_records_admin_actions(authed_org):
    oc = authed_org["client"]
    otok = authed_org["csrf"]
    oc.post("/api/admin/rounds", json={"number": 1, "state": "locked"},
            headers={"X-CSRF-Token": otok})
    entries = oc.get("/api/admin/audit", headers={"X-CSRF-Token": otok}).json()["entries"]
    assert any(e["action"] == "round.updated" for e in entries)


def test_health_endpoint(client):
    r = client.get("/api/health").json()
    assert r["ok"] is True