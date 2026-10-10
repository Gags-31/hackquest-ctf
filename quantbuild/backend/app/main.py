"""QuantBuild API — conversational UI backend.

Endpoints drive the whole lifecycle: create a project from natural language,
run the multi-agent generation pipeline, stream agent events over WebSocket,
inspect artifacts, apply natural-language modifications, preview the generated
app in the sandbox and download it as a zip.
"""
from __future__ import annotations

import asyncio
import io
import json
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from .agents.orchestrator import ProjectManagerAgent
from .config import settings
from .core.context import ProjectContext, list_projects, new_project
from .core.events import bus
from .core.llm import llm_client
from .core.sandbox import sandbox

app = FastAPI(title="QuantBuild", version="1.0.0",
              description="AI-Powered Full-Stack Architecture Designer and "
                          "Intelligent Web Application Builder")

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173",
                                                  "http://127.0.0.1:5173",
                                                  "http://localhost:8000"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

_running: dict[str, asyncio.Task] = {}


# ---------------------------------------------------------------------------
# request models
# ---------------------------------------------------------------------------

class CreateProjectRequest(BaseModel):
    requirement: str = Field(min_length=10)
    name: str | None = None


class ModifyRequest(BaseModel):
    instruction: str = Field(min_length=3)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def get_ctx_or_404(project_id: str) -> ProjectContext:
    ctx = ProjectContext.load(project_id)
    if ctx is None:
        raise HTTPException(404, f"Project '{project_id}' not found")
    return ctx


def project_state(ctx: ProjectContext) -> dict[str, Any]:
    data = asdict(ctx)
    data["file_structure"] = ctx.file_structure
    return data


async def run_pipeline_async(ctx: ProjectContext) -> None:
    loop = asyncio.get_running_loop()

    def work() -> None:
        ProjectManagerAgent(ctx).run_full_pipeline()

    task = loop.run_in_executor(None, work)
    _running[ctx.id] = asyncio.ensure_future(task)
    try:
        await _running[ctx.id]
    finally:
        _running.pop(ctx.id, None)


async def run_modification_async(ctx: ProjectContext, instruction: str) -> None:
    loop = asyncio.get_running_loop()

    def work() -> None:
        ProjectManagerAgent(ctx).run_modification(instruction)

    task = loop.run_in_executor(None, work)
    _running[ctx.id] = asyncio.ensure_future(task)
    try:
        await _running[ctx.id]
    finally:
        _running.pop(ctx.id, None)


# ---------------------------------------------------------------------------
# meta
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "QuantBuild"}


@app.get("/api/config")
def config() -> dict[str, Any]:
    return {
        "llm_provider": llm_client.provider,
        "llm_model": llm_client.model,
        "llm_online": llm_client.online,
        "max_debug_iterations": settings.max_debug_iterations,
    }


@app.get("/api/projects")
def projects() -> list[dict[str, Any]]:
    return list_projects()


# ---------------------------------------------------------------------------
# project lifecycle
# ---------------------------------------------------------------------------

@app.post("/api/projects", status_code=201)
async def create_project(req: CreateProjectRequest) -> dict[str, Any]:
    name = req.name or "Untitled App"
    ctx = new_project(name, req.requirement)
    ctx.mode = llm_client.provider
    ctx.save()
    # kick off the pipeline in the background
    asyncio.create_task(run_pipeline_async(ctx))
    return {"id": ctx.id, "name": ctx.name, "status": ctx.status}


@app.get("/api/projects/{project_id}")
def project_detail(project_id: str) -> dict[str, Any]:
    ctx = get_ctx_or_404(project_id)
    return project_state(ctx)


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str) -> dict[str, str]:
    ctx = get_ctx_or_404(project_id)
    sandbox.stop(project_id)
    import shutil
    shutil.rmtree(ctx.root, ignore_errors=True)
    return {"status": "deleted"}


@app.post("/api/projects/{project_id}/modify")
async def modify_project(project_id: str, req: ModifyRequest) -> dict[str, str]:
    ctx = get_ctx_or_404(project_id)
    if ctx.id in _running:
        raise HTTPException(409, "Pipeline already running for this project")
    asyncio.create_task(run_modification_async(ctx, req.instruction))
    return {"status": "modifying"}


# ---------------------------------------------------------------------------
# artifacts
# ---------------------------------------------------------------------------

@app.get("/api/projects/{project_id}/files")
def project_files(project_id: str) -> list[str]:
    ctx = get_ctx_or_404(project_id)
    return ctx.file_structure


@app.get("/api/projects/{project_id}/files/content")
def file_content(project_id: str, path: str) -> dict[str, str]:
    ctx = get_ctx_or_404(project_id)
    if ".." in Path(path).parts:
        raise HTTPException(400, "Invalid path")
    content = ctx.read_generated_file(path)
    if content is None:
        raise HTTPException(404, f"File '{path}' not found")
    return {"path": path, "content": content}


@app.get("/api/projects/{project_id}/download")
def download_zip(project_id: str) -> StreamingResponse:
    ctx = get_ctx_or_404(project_id)
    if not ctx.generated_dir.exists():
        raise HTTPException(409, "Project has not been generated yet")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ctx.generated_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(ctx.generated_dir))
    buffer.seek(0)
    filename = f"{ctx.name.lower().replace(' ', '-')}.zip"
    return StreamingResponse(buffer, media_type="application/zip",
                             headers={"Content-Disposition":
                                      f'attachment; filename="{filename}"'})


# ---------------------------------------------------------------------------
# sandbox preview + live website preview
# ---------------------------------------------------------------------------

PREVIEW_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>__APP_NAME__ — Live Preview · QuantBuild</title>
    <link rel="stylesheet" href="/static/preview/preview.css" />
  </head>
  <body>
    <div id="root"></div>
    <script>
      window.__QB_API_BASE__ = __API_BASE__;
      window.__QB_PREVIEW_CONFIG__ = __CONFIG_JSON__;
    </script>
    <script src="/static/preview/bundle.js"></script>
  </body>
</html>
"""

PREVIEW_NOT_RUNNING_HTML = """<!doctype html>
<html lang="en">
  <head><meta charset="UTF-8"><title>Preview not running · QuantBuild</title>
  <style>body{font-family:system-ui;background:#0c0e17;color:#e2e8f0;display:flex;
  align-items:center;justify-content:center;height:100vh;margin:0}
  .card{max-width:32rem;text-align:center;background:#181a26;border:1px solid #1e2130;
  border-radius:1rem;padding:2.5rem}
  a{color:#818cf8}</style></head>
  <body><div class="card">
    <h1>⏸ Preview not running</h1>
    <p>Start the sandbox from the QuantBuild project page
    (<strong>▶ Run in Sandbox</strong>) and then open the website preview again.</p>
    <p><a href="/">← Back to QuantBuild</a></p>
  </div></body>
</html>
"""


@app.get("/preview/{project_id}", response_class=HTMLResponse)
def preview_page(project_id: str) -> HTMLResponse:
    """Serve the generated application's website as a live preview.

    One shared bundle (built from the same templates that produced the
    generated frontend) is configured per project at render time.
    """
    ctx = get_ctx_or_404(project_id)
    status = sandbox.status(project_id)
    if not status.get("running"):
        return HTMLResponse(PREVIEW_NOT_RUNNING_HTML, status_code=409)
    from .generators.frontend_gen import entity_ui_configs

    spec = ctx.specification
    config = {
        "entityConfigs": entity_ui_configs(spec.get("entities", [])),
        "appInfo": {
            "name": spec.get("name", ctx.name),
            "appType": spec.get("app_type", "Web Application"),
            "features": spec.get("features", [])[:9],
        },
    }
    html = (PREVIEW_HTML
            .replace("__APP_NAME__", spec.get("name", ctx.name))
            .replace("__API_BASE__", json.dumps(status["url"]))
            .replace("__CONFIG_JSON__", json.dumps(config)))
    return HTMLResponse(html)


@app.post("/api/projects/{project_id}/preview")
def start_preview(project_id: str) -> dict[str, Any]:
    ctx = get_ctx_or_404(project_id)
    backend_dir = ctx.generated_dir / "backend"
    if not backend_dir.exists():
        raise HTTPException(409, "Project has not been generated yet")
    try:
        inst = sandbox.start(project_id, backend_dir)
    except RuntimeError as exc:
        raise HTTPException(500, str(exc)) from exc
    return {"running": True, "url": inst.url, "docs": f"{inst.url}/docs",
            "health": f"{inst.url}/health"}


@app.get("/api/projects/{project_id}/preview")
def preview_status(project_id: str) -> dict[str, Any]:
    return sandbox.status(project_id)


@app.delete("/api/projects/{project_id}/preview")
def stop_preview(project_id: str) -> dict[str, bool]:
    return {"stopped": sandbox.stop(project_id)}


# ---------------------------------------------------------------------------
# websocket: live agent events
# ---------------------------------------------------------------------------

@app.websocket("/ws/projects/{project_id}")
async def project_events(ws: WebSocket, project_id: str) -> None:
    await ws.accept()
    queue = bus.subscribe(project_id)
    try:
        # replay history so late joiners see the full story
        for event in bus.history(project_id):
            await ws.send_text(json.dumps(event))
        while True:
            event = await queue.get()
            await ws.send_text(json.dumps(event))
    except WebSocketDisconnect:
        pass
    finally:
        bus.unsubscribe(project_id, queue)


# ---------------------------------------------------------------------------
# static assets (live-preview bundle) + optional built frontend
# ---------------------------------------------------------------------------

from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
