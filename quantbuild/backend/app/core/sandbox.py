"""Application preview sandbox.

Runs a generated backend in an isolated subprocess (own working directory,
own SQLite database file, dedicated port) so generated applications can be
built, run, tested and validated safely before deployment.
"""
from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from ..config import settings


@dataclass
class PreviewInstance:
    project_id: str
    port: int
    process: subprocess.Popen
    started_at: float = field(default_factory=time.time)
    url: str = ""


class SandboxManager:
    def __init__(self) -> None:
        self._previews: dict[str, PreviewInstance] = {}

    def _free_port(self) -> int:
        for port in range(settings.preview_port_start, settings.preview_port_end + 1):
            if port in (p.port for p in self._previews.values()):
                continue
            with socket.socket() as sock:
                if sock.connect_ex(("127.0.0.1", port)) != 0:
                    return port
        raise RuntimeError("No free preview ports")

    def start(self, project_id: str, backend_dir: Path) -> PreviewInstance:
        self.stop(project_id)
        port = self._free_port()
        env = {"DATABASE_URL": f"sqlite:///{backend_dir / 'preview.db'}",
               # allow the QuantBuild-hosted live preview page to call the API
               "CORS_ORIGINS": "http://localhost:5173,http://localhost:8000,"
                               "http://127.0.0.1:8000,http://127.0.0.1:5173",
               "PATH": __import__("os").environ.get("PATH", ""),
               "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", ""),
               "PYTHONPATH": str(backend_dir)}

        # fresh database + demo data so the preview has instant content
        for stale in ("preview.db",):
            try:
                (backend_dir / stale).unlink(missing_ok=True)
            except OSError:
                pass
        seed = subprocess.run([sys.executable, "-m", "app.seed"],
                              cwd=backend_dir, env=env,
                              capture_output=True, text=True, timeout=120)

        log = open(backend_dir / "preview.log", "w", encoding="utf-8")
        if seed.returncode != 0:
            log.write("SEED FAILED (continuing with an empty database)\n")
            log.write(seed.stdout + "\n" + seed.stderr + "\n")
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app",
             "--host", "127.0.0.1", "--port", str(port)],
            cwd=backend_dir, stdout=log, stderr=subprocess.STDOUT,
            env=env,
        )
        inst = PreviewInstance(project_id, port, proc, url=f"http://127.0.0.1:{port}")
        self._previews[project_id] = inst

        # wait until healthy (max ~15s)
        deadline = time.time() + 15
        while time.time() < deadline:
            if proc.poll() is not None:
                self.stop(project_id)
                raise RuntimeError(f"Preview process exited early; see {log.name}")
            try:
                with urllib.request.urlopen(f"{inst.url}/health", timeout=1) as resp:
                    if resp.status == 200:
                        return inst
            except Exception:
                time.sleep(0.4)
        self.stop(project_id)
        raise RuntimeError("Preview did not become healthy in 15s")

    def stop(self, project_id: str) -> bool:
        inst = self._previews.pop(project_id, None)
        if not inst:
            return False
        if inst.process.poll() is None:
            inst.process.terminate()
            try:
                inst.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                inst.process.kill()
        return True

    def stop_all(self) -> None:
        for project_id in list(self._previews):
            self.stop(project_id)

    def status(self, project_id: str) -> dict:
        inst = self._previews.get(project_id)
        if not inst:
            return {"running": False}
        alive = inst.process.poll() is None
        return {"running": alive, "url": inst.url, "port": inst.port,
                "uptime_seconds": round(time.time() - inst.started_at, 1)}


sandbox = SandboxManager()

import atexit

atexit.register(sandbox.stop_all)
