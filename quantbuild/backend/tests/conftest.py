"""Shared fixtures: a fully generated e-commerce project (module-scoped)."""
import shutil

import pytest

from app.agents.orchestrator import ProjectManagerAgent
from app.core.context import new_project

ECOMMERCE = ("Build an e-commerce platform where customers can browse products, "
             "add items to a cart, make payments and track their orders.")


@pytest.fixture(scope="module")
def project():
    ctx = new_project("PytestShop", ECOMMERCE)
    ProjectManagerAgent(ctx).run_full_pipeline()
    yield ctx
    # teardown: remove the generated project from the workspace
    shutil.rmtree(ctx.root, ignore_errors=True)
