"""API surface tests for the QuantBuild server itself."""
import asyncio

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_config_reports_offline_mode():
    resp = client.get("/api/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["llm_provider"] in ("offline", "openai", "anthropic", "ollama")


def test_create_and_poll_project():
    resp = client.post("/api/projects", json={
        "requirement": "Create a personal finance manager where users track "
                       "expenses, set budgets and view spending reports.",
        "name": "FinTest",
    })
    assert resp.status_code == 201, resp.text
    project_id = resp.json()["id"]

    # wait for the background pipeline (runs in an executor)
    for _ in range(120):
        resp = client.get(f"/api/projects/{project_id}")
        if resp.json()["status"] in ("generated", "failed"):
            break
        import time
        time.sleep(2)
    body = resp.json()
    assert body["status"] == "generated"
    assert body["specification"]["app_type"] == "Personal Finance Manager"
    assert body["validation"]["ok"] is True
    assert len(body["file_structure"]) > 40

    # file listing + content
    resp = client.get(f"/api/projects/{project_id}/files")
    assert resp.status_code == 200 and "backend/app/main.py" in resp.json()
    resp = client.get(f"/api/projects/{project_id}/files/content",
                      params={"path": "backend/app/main.py"})
    assert resp.status_code == 200 and "FastAPI" in resp.json()["content"]

    # traversal guard
    resp = client.get(f"/api/projects/{project_id}/files/content",
                      params={"path": "../project.json"})
    assert resp.status_code == 400

    # download zip
    resp = client.get(f"/api/projects/{project_id}/download")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert len(resp.content) > 10_000

    # modify
    resp = client.post(f"/api/projects/{project_id}/modify",
                       json={"instruction": "Add invoice tracking"})
    assert resp.status_code == 200
    for _ in range(120):
        resp = client.get(f"/api/projects/{project_id}")
        if resp.json()["status"] == "generated":
            break
        import time
        time.sleep(2)
    assert resp.json()["status"] == "generated"

    # delete
    resp = client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 200
    assert client.get(f"/api/projects/{project_id}").status_code == 404


def test_live_website_preview(project):
    """The generated app's website renders as a live preview."""
    from app.core.sandbox import sandbox

    backend_dir = project.generated_dir / "backend"
    inst = sandbox.start(project.id, backend_dir)
    try:
        resp = client.get(f"/preview/{project.id}")
        assert resp.status_code == 200
        assert "__QB_PREVIEW_CONFIG__" in resp.text
        assert "__QB_API_BASE__" in resp.text
        assert "bundle.js" in resp.text
        # static assets are served
        assert client.get("/static/preview/bundle.js").status_code == 200
        assert client.get("/static/preview/preview.css").status_code == 200
    finally:
        sandbox.stop(project.id)


def test_preview_page_when_sandbox_down():
    resp = client.get("/preview/pytestshop-does-not-exist")
    assert resp.status_code == 404  # project itself missing → 404


def test_unknown_project_404():
    assert client.get("/api/projects/nope-nope-nope").status_code == 404
