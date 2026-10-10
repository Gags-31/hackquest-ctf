"""End-to-end offline pipeline tests.

Runs the full multi-agent pipeline on a realistic requirement and asserts the
generated application is structurally complete, valid and tested.
"""
import json
from pathlib import Path

import pytest

from app.agents.orchestrator import ProjectManagerAgent
from app.core.context import ProjectContext, new_project

ECOMMERCE = ("Build an e-commerce platform where customers can browse products, "
             "add items to a cart, make payments and track their orders.")


@pytest.fixture(scope="module")
def project() -> ProjectContext:
    ctx = new_project("PytestShop", ECOMMERCE)
    ProjectManagerAgent(ctx).run_full_pipeline()
    yield ctx
    # teardown: remove the generated project from the workspace
    import shutil
    shutil.rmtree(ctx.root, ignore_errors=True)


def test_pipeline_completes(project):
    assert project.status == "generated"
    assert project.specification["app_type"] == "E-Commerce Platform"


def test_central_context_is_complete(project):
    assert project.architecture["style"]
    assert project.architecture["diagram"].startswith("flowchart")
    assert project.database_schema["sql"].startswith("--")
    assert project.database_schema["er_diagram"].startswith("erDiagram")
    assert project.api_contract["openapi"]["openapi"] == "3.0.3"
    assert project.ui_design["pages"]
    assert project.tech_stack["backend"]["framework"] == "FastAPI"


def test_validation_and_tests_green(project):
    assert project.validation["ok"] is True
    assert project.tests["result"]["ok"] is True
    assert project.tests["result"]["failed"] == 0
    assert project.tests["result"]["passed"] > 10


def test_security_report(project):
    assert project.security["score"] >= 75
    assert project.security["checks_passed"]


def test_generated_structure(project):
    expected = [
        "backend/app/main.py", "backend/app/models.py", "backend/app/schemas.py",
        "backend/app/security.py", "backend/app/routers/auth.py",
        "backend/tests/conftest.py", "backend/tests/test_auth.py",
        "frontend/package.json", "frontend/src/App.tsx",
        "migrations/0001_init.sql", "docker-compose.yml",
        "backend/Dockerfile", "frontend/Dockerfile",
        ".github/workflows/ci.yml", "README.md", "docs/API.md",
        "docs/ARCHITECTURE.md", "docs/DATABASE.md", "openapi.json",
    ]
    for path in expected:
        assert path in project.file_structure, f"missing {path}"


def test_generated_backend_is_consistent(project):
    """Every entity has a router, and the OpenAPI contract matches."""
    entities = [e for e in project.specification["entities"] if e["name"] != "User"]
    for ent in entities:
        assert f"backend/app/routers/{ent['table']}.py" in project.file_structure
    openapi = project.api_contract["openapi"]
    assert "/api/auth/register" in openapi["paths"]
    assert "/api/auth/login" in openapi["paths"]


def test_modification_add_wishlist(project):
    before = len(project.specification["entities"])
    result = ProjectManagerAgent(project).run_modification("Add a wishlist feature")
    assert "Wishlist" in result["analysis"]["new_entities"]
    after = project.specification["entities"]
    assert len(after) == before + 2  # Wishlist + WishlistItem
    names = {e["name"] for e in after}
    assert {"Wishlist", "WishlistItem"} <= names
    assert project.validation["ok"] is True
    assert project.tests["result"]["ok"] is True
    assert "backend/app/routers/wishlists.py" in project.file_structure


def test_project_persistence(project):
    loaded = ProjectContext.load(project.id)
    assert loaded is not None
    assert loaded.name == project.name
    assert loaded.specification["app_type"] == project.specification["app_type"]
