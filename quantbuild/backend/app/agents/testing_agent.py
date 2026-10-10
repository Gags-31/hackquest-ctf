"""Testing Agent — generates and executes the test suite.

Maintains requirement → feature → code → test traceability, then runs the
generated pytest suite inside the validation pipeline.
"""
from __future__ import annotations

from typing import Any

from .base import BaseAgent
from ..core import validation


class TestingAgent(BaseAgent):
    name = "Testing Agent"
    stage = "testing"

    def run(self) -> dict[str, Any]:
        from .backend_agent import TestGenerator  # deferred to avoid a cycle

        self.start("Generating test cases from requirements")
        written = TestGenerator.write_tests(self.ctx)

        spec = self.ctx.specification
        traceability = []
        for feat in spec.get("features", [])[:20]:
            linked = "test_auth.py" if any(k in feat.lower() for k in
                                           ("regist", "login", "auth")) else \
                next((f"test_{e['table']}.py" for e in spec["entities"]
                      if e["name"].lower() in feat.lower()), "test suite")
            traceability.append({"requirement": feat, "test_file": linked})

        self.think(f"Executing {len(written)} test files (pytest)")
        report = validation.ValidationReport()
        result = validation.run_tests(self.ctx.generated_dir / "backend", report)

        self.ctx.tests = {
            "files": written,
            "traceability": traceability,
            "result": result,
            "passed": result.get("ok") is True,
        }
        self.ctx.save()
        if result.get("ok"):
            self.done(f"All tests passed ({result.get('passed', 0)} tests)")
        else:
            self.done(f"Tests failed: {result.get('failed', '?')} failing",
                      detail={"failures": report.to_dict()["findings"]})
        return self.ctx.tests
