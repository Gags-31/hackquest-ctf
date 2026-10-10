"""Central Project Context / Architecture Memory.

Every agent reads and writes this shared representation, which keeps the
architecture, database schema, API contract, generated code, dependencies,
tests and known issues consistent with each other.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from ..config import WORKSPACE_DIR
from .events import bus, PipelineEvent


@dataclass
class ProjectContext:
    """The single source of truth for a generated application."""

    id: str
    name: str
    requirement: str = ""                       # raw natural-language requirement
    mode: str = "offline"                       # llm provider actually used
    status: str = "created"                     # created | generating | generated | failed | modifying
    created_at: float = field(default_factory=time.time)

    # Structured knowledge built by the agents
    specification: dict[str, Any] = field(default_factory=dict)   # Requirement Agent
    architecture: dict[str, Any] = field(default_factory=dict)    # Architecture Agent
    tech_stack: dict[str, Any] = field(default_factory=dict)      # Technology selection
    database_schema: dict[str, Any] = field(default_factory=dict) # Database Agent
    api_contract: dict[str, Any] = field(default_factory=dict)    # API Agent (OpenAPI)
    ui_design: dict[str, Any] = field(default_factory=dict)       # UI/UX Agent
    file_structure: list[str] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    tests: dict[str, Any] = field(default_factory=dict)           # Testing Agent
    validation: dict[str, Any] = field(default_factory=dict)      # validation pipeline
    security: dict[str, Any] = field(default_factory=dict)        # Security Agent
    documentation: dict[str, str] = field(default_factory=dict)   # Documentation Agent
    deployment: dict[str, Any] = field(default_factory=dict)      # Deployment Agent
    known_issues: list[str] = field(default_factory=list)
    modifications: list[dict[str, Any]] = field(default_factory=list)
    impact_analyses: list[dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------ persistence
    @property
    def root(self) -> Path:
        return WORKSPACE_DIR / self.id

    @property
    def generated_dir(self) -> Path:
        return self.root / "generated"

    def save(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        # atomic write: never leave a partially-written project.json behind
        tmp = self.root / "project.json.tmp"
        tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        tmp.replace(self.root / "project.json")

    @classmethod
    def load(cls, project_id: str, *, _retries: int = 3) -> "ProjectContext | None":
        path = WORKSPACE_DIR / project_id / "project.json"
        if not path.exists():
            return None
        data = None
        for attempt in range(_retries):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                break
            except json.JSONDecodeError:
                if attempt == _retries - 1:
                    return None
                time.sleep(0.15)
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})

    # ------------------------------------------------------------ event sugar
    def emit(self, agent: str, stage: str, status: str, message: str,
             detail: dict[str, Any] | None = None) -> None:
        bus.emit(PipelineEvent(self.id, agent, stage, status, message, detail or {}))

    # ------------------------------------------------------------ file output
    def write_generated_file(self, rel_path: str, content: str) -> None:
        """Write a file of the *generated application* and track it."""
        target = self.generated_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        rel = str(Path(rel_path).as_posix())
        if rel not in self.file_structure:
            self.file_structure.append(rel)
            self.file_structure.sort()

    def read_generated_file(self, rel_path: str) -> str | None:
        target = self.generated_dir / rel_path
        if target.exists() and target.is_file():
            return target.read_text(encoding="utf-8", errors="replace")
        return None


# ------------------------------------------------------------------- registry
def new_project(name: str, requirement: str) -> ProjectContext:
    slug = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-") or "app"
    slug = "-".join(p for p in slug.split("-") if p)[:40]
    project_id = f"{slug}-{uuid.uuid4().hex[:8]}"
    ctx = ProjectContext(id=project_id, name=name, requirement=requirement)
    ctx.save()
    return ctx


def list_projects() -> list[dict[str, Any]]:
    projects = []
    for path in sorted(WORKSPACE_DIR.iterdir() if WORKSPACE_DIR.exists() else []):
        if (path / "project.json").exists():
            ctx = ProjectContext.load(path.name)
            if ctx:
                projects.append({
                    "id": ctx.id,
                    "name": ctx.name,
                    "status": ctx.status,
                    "app_type": ctx.specification.get("app_type", ""),
                    "created_at": ctx.created_at,
                    "requirement": ctx.requirement,
                })
    projects.sort(key=lambda p: p["created_at"], reverse=True)
    return projects
