from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["healthy"] is True


def test_agent_run():
    r = client.post("/agents/run", json={"agent": "nlp", "messages": ["I need 50 units, budget ₹2 lakh, delivery before the 20th"]})
    data = r.json()
    assert data["agent"] == "nlp"
    assert data["entities"]["quantity"] == "50 units"


def test_customer_flow():
    r = client.post("/customers/", params={"name": "Test"})
    cid = r.json()["id"]
    r = client.post("/conversations/", params={"customer_id": cid}, json=["I need 10 units before Monday"])
    assert r.status_code == 200
    r = client.post("/proposals/generate", params={"customer_id": cid}, json=["I need 10 units, budget ₹1 lakh"])
    assert "proposal" in r.json()
