"""Architecture Agent — designs the system architecture.

Chooses an architecture style (monolithic / modular monolith / microservices /
event-driven / serverless), selects the technology stack, explains the
reasoning, and renders a Mermaid architecture diagram from the specification.
"""
from __future__ import annotations

from typing import Any

from .base import BaseAgent


class ArchitectureAgent(BaseAgent):
    name = "Architecture Agent"
    stage = "architecture_design"

    def run(self) -> dict[str, Any]:
        spec = self.ctx.specification
        self.start("Designing system architecture")

        self.think("Retrieving architecture knowledge (RAG)")
        self.rag("modular monolith microservices choosing an architecture", top_k=2)

        style, rationale = self._choose_style(spec)
        components = self._components(spec, style)
        layers = [
            {"name": "Presentation", "technology": "React + TypeScript + Tailwind CSS",
             "responsibility": "Pages, components, routing, client state"},
            {"name": "API", "technology": "FastAPI (REST, OpenAPI)",
             "responsibility": "Routing, validation, authentication, RBAC"},
            {"name": "Service", "technology": "Python service layer",
             "responsibility": "Business logic, transactions, orchestration"},
            {"name": "Data", "technology": "SQLAlchemy + SQLite/PostgreSQL",
             "responsibility": "Models, relationships, migrations"},
        ]
        diagram = self._mermaid(spec, style, components)

        architecture = {
            "style": style,
            "rationale": rationale,
            "components": components,
            "layers": layers,
            "communication": "Synchronous REST/JSON over HTTPS",
            "diagram": diagram,
            "deployment_topology": "Single container for development; web/worker/db "
                                   "split available for production",
        }
        self.ctx.architecture = architecture
        self.ctx.tech_stack = self._tech_stack(spec)
        self.ctx.save()
        self.done(f"Selected {style} architecture with {len(components)} components",
                  detail={"style": style})
        return architecture

    # --------------------------------------------------------------- decisions
    def _choose_style(self, spec: dict[str, Any]) -> tuple[str, str]:
        entities = len(spec.get("entities", []))
        features = len(spec.get("features", []))
        if entities >= 14 or features >= 18:
            return ("Microservices",
                    f"The domain decomposes into {entities} entities and {features} features "
                    "with distinct scaling profiles (catalog, orders, notifications), so "
                    "independently deployable services are justified.")
        if entities >= 6 or features >= 8:
            return ("Modular Monolith",
                    f"With {entities} entities and {features} features the system benefits from "
                    "clear module boundaries (identity, catalog, orders, notifications) while "
                    "staying simple to build, test and deploy as one unit — the recommended "
                    "default for a production-oriented MVP.")
        return ("Monolithic",
                f"A compact domain ({entities} entities, {features} features) is best served by a "
                "single well-layered application: fast to develop, trivial to deploy, easy to "
                "refactor into modules later.")

    def _components(self, spec: dict[str, Any], style: str) -> list[dict[str, str]]:
        names = [e["name"] for e in spec.get("entities", [])]
        components = [
            {"name": "Web Client", "kind": "frontend",
             "description": "React single-page application served to the browser"},
            {"name": "API Server", "kind": "backend",
             "description": "FastAPI application exposing the REST API contract"},
            {"name": "Auth Module", "kind": "service",
             "description": "JWT issuance/verification, password hashing, RBAC guards"},
            {"name": "Database", "kind": "database",
             "description": "Relational store (SQLite dev / PostgreSQL production)"},
        ]
        domain_modules = sorted({n for n in names if n != "User"})
        for mod in domain_modules[:8]:
            components.append({"name": f"{mod} Module", "kind": "service",
                               "description": f"CRUD and business rules for {mod}"})
        if any("Notification" in n for n in names):
            components.append({"name": "Notification Module", "kind": "service",
                               "description": "In-app notification creation and delivery"})
        return components

    def _tech_stack(self, spec: dict[str, Any]) -> dict[str, Any]:
        return {
            "frontend": {"framework": "React 18", "language": "TypeScript",
                         "bundler": "Vite", "styling": "Tailwind CSS"},
            "backend": {"framework": "FastAPI", "language": "Python 3.11+",
                        "orm": "SQLAlchemy 2.0", "validation": "Pydantic v2"},
            "database": {"development": "SQLite", "production": "PostgreSQL"},
            "authentication": {"tokens": "JWT (HS256)", "passwords": "PBKDF2-HMAC-SHA256"},
            "testing": {"backend": "pytest + FastAPI TestClient", "api": "OpenAPI contract"},
            "deployment": {"containers": "Docker", "orchestration": "Docker Compose",
                           "ci": "GitHub Actions"},
            "reasoning": ("The stack favours strong typing across the boundary (Pydantic ↔ "
                          "TypeScript), a first-class OpenAPI contract, minimal operational "
                          "friction for development (SQLite) and a production path via "
                          "PostgreSQL and containers."),
        }

    # ---------------------------------------------------------------- diagram
    def _mermaid(self, spec: dict[str, Any], style: str,
                 components: list[dict[str, str]]) -> str:
        services = [c for c in components if c["kind"] == "service"]
        lines = [
            "flowchart TD",
            '    CLIENT["🖥️ React SPA<br/>TypeScript + Tailwind"]',
            '    API["⚡ FastAPI Server<br/>REST + OpenAPI"]',
            '    AUTH["🔐 Auth Module<br/>JWT + RBAC"]',
            '    DB[("🗄️ Database<br/>SQLite / PostgreSQL")]',
        ]
        for i, svc in enumerate(services):
            node = f"SVC{i}"
            label = svc["name"].replace('"', "'")
            lines.append(f'    {node}["🧩 {label}"]')
        lines.append("    CLIENT -->|HTTPS / JSON| API")
        lines.append("    API --> AUTH")
        for i in range(len(services)):
            lines.append(f"    API --> SVC{i}")
            lines.append(f"    SVC{i} --> DB")
        lines.append("    AUTH --> DB")
        lines.append(f'    subgraph STYLE["🏗️ {style}"]')
        lines.append("        API")
        lines.append("    end")
        return "\n".join(lines)
