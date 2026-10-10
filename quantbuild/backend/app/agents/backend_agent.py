"""Backend Agent — generates the FastAPI backend codebase.

Routes, controllers (CRUD helpers), services, models, authentication,
validation — all driven by the Central Project Context so the backend stays
consistent with the database schema and API contract.
"""
from __future__ import annotations

from typing import Any

from .base import BaseAgent
from ..core.nlp import to_table_name
from ..generators import backend_gen, tests_gen


class BackendAgent(BaseAgent):
    name = "Backend Agent"
    stage = "backend_generation"

    def run(self) -> list[str]:
        spec = self.ctx.specification
        entities: list[dict[str, Any]] = spec["entities"]
        self.start(f"Generating FastAPI backend for {len(entities)} entities")
        self.rag("fastapi routers dependency injection pydantic sqlalchemy", top_k=2)

        written: list[str] = []

        def w(path: str, content: str) -> None:
            self.ctx.write_generated_file(path, content)
            written.append(path)

        w("backend/requirements.txt", backend_gen.render_requirements())
        w("backend/app/__init__.py", backend_gen.render_app_init())
        w("backend/app/config.py", backend_gen.render_config(spec))
        w("backend/app/database.py", backend_gen.render_database())
        w("backend/app/security.py", backend_gen.render_security())
        w("backend/app/models.py", backend_gen.render_models(entities))
        w("backend/app/schemas.py", backend_gen.render_schemas(entities))
        w("backend/app/crud.py", backend_gen.render_crud())
        w("backend/app/routers/__init__.py", backend_gen.render_routers_init())
        w("backend/app/routers/auth.py", backend_gen.render_auth_router(spec))
        w("backend/app/routers/users.py", backend_gen.render_users_router())
        for ent in entities:
            if ent["name"] == "User":
                continue
            w(f"backend/app/routers/{ent['table']}.py",
              backend_gen.render_entity_router(ent))
        w("backend/app/main.py", backend_gen.render_main(spec, entities))
        w("backend/app/seed.py", backend_gen.render_seed(spec, entities))
        # SQL migration from the Database Agent
        if self.ctx.database_schema.get("sql"):
            w("migrations/0001_init.sql", self.ctx.database_schema["sql"])

        self.ctx.dependencies["backend"] = ["fastapi", "uvicorn", "sqlalchemy", "pydantic"]
        self.ctx.save()
        self.done(f"Backend generated: {len(written)} files "
                  f"({len(entities) - 1} resource routers + auth + users)")
        return written


class TestGenerator:
    """Used by the Testing Agent to materialise the pytest suite."""

    @staticmethod
    def write_tests(ctx) -> list[str]:
        entities = ctx.specification["entities"]
        written = []
        ctx.write_generated_file("backend/tests/__init__.py", tests_gen.render_test_init())
        written.append("backend/tests/__init__.py")
        ctx.write_generated_file("backend/tests/conftest.py", tests_gen.render_conftest())
        written.append("backend/tests/conftest.py")
        ctx.write_generated_file("backend/tests/test_auth.py", tests_gen.render_test_auth())
        written.append("backend/tests/test_auth.py")
        for ent in entities:
            if ent["name"] == "User":
                continue
            path = f"backend/tests/test_{to_table_name(ent['name'])}.py"
            ctx.write_generated_file(path, tests_gen.render_test_entity(ent, entities))
            written.append(path)
        return written
