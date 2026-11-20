"""Acceptance tests for the 26 required verification cases."""
import re

from .conftest import csrf, headers, login, register


def _alpha(client):
    assert login(client, "Alpha Two").status_code == 200


def test_01_register_two_members(client):
    r = register(client, "Alpha Two", 1)
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "pending"
    from app.db import SessionLocal
    from app.models import Team
    db = SessionLocal()
    team = db.query(Team).filter_by(name="Alpha Two").first()
    assert len(team.members) == 2
    db.close()


def test_02_register_three_members(client):
    assert register(client, "Beta Three", 2).status_code == 201


def test_03_register_four_members(client):
    assert register(client, "Gamma Four", 3).status_code == 201


def test_04_reject_one_member(client):
    assert register(client, "Delta One", 0).status_code == 400


def test_05_reject_five_members(client):
    assert register(client, "Epsilon Five", 4).status_code == 400


def test_06_duplicate_emails_rejected(client):
    r = client.post("/api/auth/register", json={
        "team_name": "Duplicate Mail", "college": "KLEIT", "department": "CSE",
        "semester": "4", "leader_name": "Dup Leader",
        "leader_email": "dup@example.com", "password": "TeamPass!2026",
        "members": [
            {"name": "Dup One", "email": "dup@example.com", "mobile": "9000000001"},
            {"name": "Dup Two", "email": "other@example.com", "mobile": "9000000002"},
        ],
    })
    assert r.status_code == 400


def test_07_unique_codes(org_client):
    codes = [t["code"] for t in org_client.get("/api/admin/teams").json()]
    assert len(codes) == len(set(codes))
    assert all(re.fullmatch(r"HQ-[A-Z2-9]{6}", c) for c in codes)


def test_08_correct_team_auth(client, org_client):
    org_client.post("/api/admin/teams/1/approve")
    _alpha(client)
    assert client.get("/api/team/me").json()["team"]["name"] == "Alpha Two"


def test_09_code_cannot_replace_password(client):
    _alpha(client)
    code = client.get("/api/team/me").json()["team"]["code"]
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={
        "username": "Alpha Two", "password": code}).status_code == 401


def test_10_future_rounds_locked(client, org_client):
    org_client.post("/api/admin/teams/3/approve")
    assert login(client, "Gamma Four").status_code == 200
    states = {r["number"]: r for r in client.get("/api/team/state").json()["rounds"]}
    assert states[1]["state"] == "locked"
    assert states[4]["state"] == "locked"
    assert client.get("/api/team/challenge/binary-signal").status_code == 403


def test_11_round_activation(org_client, client):
    h = headers(org_client)
    org_client.post("/api/admin/rounds/1/end", headers=h)
    r = org_client.post("/api/admin/rounds/1/start", headers=h)
    assert r.status_code == 200, r.text
    _alpha(client)
    states = {x["number"]: x for x in client.get("/api/team/state").json()["rounds"]}
    assert states[1]["state"] == "open"
    assert states[2]["state"] == "locked"
    assert client.get("/api/team/challenge/binary-signal").status_code == 200


def test_12_server_time_timer(client):
    _alpha(client)
    a = client.get("/api/team/state").json()
    b = client.get("/api/team/state").json()
    assert "server_now" in a and "server_now" in b
    first = next(x for x in a["rounds"] if x["number"] == 1)["remaining_seconds"]
    second = next(x for x in b["rounds"] if x["number"] == 1)["remaining_seconds"]
    assert isinstance(first, int) and 0 < first <= 3000
    assert second <= first


def test_13_14_correct_flag_awards_points(client):
    _alpha(client)
    r = client.post("/api/team/submit", headers={**headers(client), "x-challenge": "binary-signal"},
                    json={"flag": "HQCTF{hunch}"})
    assert r.status_code == 200 and r.json()["correct"] is True, r.text
    assert r.json()["points"] == 100
    assert client.get("/api/team/me").json()["solved"] == 1


def test_15_incorrect_flag_no_points(client):
    _alpha(client)
    before = client.get("/api/team/me").json()["score"]
    r = client.post("/api/team/submit",
                    headers={**headers(client), "x-challenge": "hex-trail"},
                    json={"flag": "HQCTF{wrong}"})
    assert r.json()["correct"] is False
    assert client.get("/api/team/me").json()["score"] == before


def test_16_duplicate_correct_no_double_points(client):
    _alpha(client)
    before = client.get("/api/team/me").json()["score"]
    r = client.post("/api/team/submit",
                    headers={**headers(client), "x-challenge": "binary-signal"},
                    json={"flag": "HQCTF{hunch}"})
    assert r.json()["already_solved"] is True
    assert client.get("/api/team/me").json()["score"] == before


def test_17_hints_restricted(client):
    _alpha(client)
    detail = client.get("/api/team/challenge/hex-trail").json()
    assert len(detail["hints"]) == 2
    assert all("HQCTF{" not in h["text"] for h in detail["hints"])
    assert client.post("/api/team/hint/hex-trail/1", headers=headers(client)).status_code == 200


def test_18_solutions_not_exposed(client):
    _alpha(client)
    for path in ("/api/team/challenges", "/api/team/challenge/hex-trail",
                 "/api/public/rounds", "/api/public/event"):
        body = client.get(path).text
        assert "HQCTF{hex_map}" not in body
        assert '"solution"' not in body.lower()
        assert '"flag"' not in body.lower()


def test_19_scoreboard_updates(org_client):
    alpha = next(r for r in org_client.get("/api/admin/scoreboard").json()["rows"]
                 if r["team"] == "Alpha Two")
    assert alpha["total"] >= 100 and alpha["round1"] >= 100


def test_20_participants_cannot_access_scoreboard(client):
    _alpha(client)
    for path in ("/api/admin/scoreboard", "/api/admin/scoreboard.csv",
                 "/api/admin/challenges", "/api/admin/overview"):
        assert client.get(path).status_code == 403


def test_21_both_organisers(org_client, coorg_client):
    assert org_client.get("/api/admin/overview").status_code == 200
    assert coorg_client.get("/api/admin/overview").status_code == 200
    accounts = org_client.get("/api/admin/accounts").json()
    assert {a["username"] for a in accounts} == {"pragyan_lead", "ieee_lead"}
    assert all(a["must_change_password"] for a in accounts)


def test_22_admin_authorization(client):
    _alpha(client)
    assert client.post("/api/admin/rounds/2/start", headers=headers(client)).status_code == 403
    assert client.get("/api/admin/teams").status_code == 403


def test_23_pause_resume(org_client, client):
    h = headers(org_client)
    org_client.post("/api/admin/rounds/1/pause", headers=h)
    _alpha(client)
    assert next(x for x in client.get("/api/team/state").json()["rounds"]
                if x["number"] == 1)["state"] == "paused"
    assert client.post("/api/team/submit",
                       headers={**headers(client), "x-challenge": "hex-trail"},
                       json={"flag": "HQCTF{hex_map}"}).status_code == 409
    org_client.post("/api/admin/rounds/1/resume", headers=h)
    assert next(x for x in client.get("/api/team/state").json()["rounds"]
                if x["number"] == 1)["state"] == "open"


def test_24_riddles_and_memes(client, org_client):
    data = client.get("/api/public/break/1").json()
    assert data["riddle"] and "?" in data["riddle"]["question"]
    assert data["meme"] and data["meme"]["caption"]
    assert client.get("/api/public/reveal/1").status_code == 403
    assert len(org_client.get("/api/admin/riddles").json()) >= 20


def test_25_exports(org_client):
    csv = org_client.get("/api/admin/scoreboard.csv")
    assert csv.status_code == 200 and b"Rank" in csv.content
    pdf = org_client.get("/api/admin/scoreboard.pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


def test_26_full_simulation(org_client, client):
    h = headers(org_client)
    for t in org_client.get("/api/admin/teams").json():
        if t["status"] == "pending":
            org_client.post(f"/api/admin/teams/{t['id']}/approve", headers=h)
    assert login(client, "Beta Three").status_code == 200
    me = client.get("/api/team/me").json()
    assert me["score"] == 0
    assert len(me["team"]["members"]) == 3
    r = client.post("/api/team/submit",
                    headers={**headers(client), "x-challenge": "hex-trail"},
                    json={"flag": "HQCTF{hex_map}"})
    assert r.json()["correct"] is True, r.text
    assert client.get("/api/team/me").json()["score"] == 100
    rows = org_client.get("/api/admin/scoreboard").json()["rows"]
    assert len(rows) >= 3
    assert {x["team"] for x in rows} >= {"Alpha Two", "Beta Three", "Gamma Four"}
