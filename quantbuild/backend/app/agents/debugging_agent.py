"""Debugging Agent — autonomous error analysis and repair loop.

Consumes error logs, stack traces and test failures from the validation
pipeline, generates candidate fixes (LLM when configured, deterministic
repair heuristics otherwise), applies them and re-runs the validation until
green or the iteration budget is exhausted.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base import BaseAgent
from ..config import settings
from ..core import validation


class DebuggingAgent(BaseAgent):
    name = "Debugging Agent"
    stage = "debugging"

    def run(self) -> dict[str, Any]:
        self.start("Running validation pipeline (syntax → dependencies → static → build → tests)")
        history: list[dict[str, Any]] = []
        backend_dir = self.ctx.generated_dir / "backend"

        for iteration in range(1, settings.max_debug_iterations + 1):
            report, test_result = validation.full_pipeline(backend_dir)
            history.append({"iteration": iteration, "report": report.to_dict(),
                            "tests": {k: v for k, v in test_result.items() if k != "output"}})
            self.think(f"Validation iteration {iteration}: "
                       f"{'OK' if report.ok and test_result.get('ok') else 'errors found'}")

            if report.ok and test_result.get("ok"):
                self.ctx.validation = {"ok": True, "iterations": iteration,
                                       "history": history}
                if self.ctx.tests.get("result") is not None:
                    self.ctx.tests["result"] = {**test_result,
                                                "output": test_result.get("output", "")[-2000:]}
                    self.ctx.tests["passed"] = True
                self.ctx.save()
                self.done(f"Validation passed after {iteration} iteration(s) — "
                          f"{test_result.get('passed', 0)} tests green")
                return self.ctx.validation

            errors = [f for f in report.findings if f.severity == "error"]
            if test_result.get("ok") is False:
                errors.extend(self._parse_pytest_failures(test_result.get("output", "")))
            if not errors:
                break
            fixed = self._attempt_fixes(backend_dir, errors, test_result.get("output", ""))
            if not fixed:
                self.think("No automatic fix available for the remaining errors")
                break
            self.think(f"Applied {fixed} fix(es); re-validating")

        self.ctx.validation = {"ok": False, "iterations": len(history),
                               "history": history}
        self.ctx.known_issues.append("Validation did not fully pass; see debugging history")
        self.ctx.save()
        self.fail("Validation still failing after the debugging loop",
                  detail={"iterations": len(history)})
        return self.ctx.validation

    # ------------------------------------------------------------------ fixing
    def _parse_pytest_failures(self, output: str) -> list[validation.Finding]:
        findings: list[validation.Finding] = []
        for line in output.splitlines():
            if line.startswith("FAILED"):
                findings.append(validation.Finding("tests", "error", line))
            elif re.match(r"^(E\s+)?(AssertionError|KeyError|TypeError|AttributeError|"
                          r"NameError|ImportError|ModuleNotFoundError)", line.strip()):
                findings.append(validation.Finding("tests", "error", line.strip()[:300]))
        return findings[:20]

    def _attempt_fixes(self, backend_dir: Path,
                       errors: list[validation.Finding], test_output: str) -> int:
        """Deterministic repair heuristics; returns how many fixes were applied."""
        fixes = 0
        for finding in errors:
            message = finding.message
            # 1. missing dependency → append to requirements.txt
            m = re.search(r"No module named '([a-zA-Z0-9_]+)'", message)
            if m:
                module = m.group(1)
                req = backend_dir / "requirements.txt"
                current = req.read_text(encoding="utf-8") if req.exists() else ""
                if module not in current:
                    req.write_text(current.rstrip() + f"\n{module}\n", encoding="utf-8")
                    fixes += 1
                continue
            # 2. LLM-assisted repair when available
            if self.llm_online and finding.file:
                path = backend_dir / finding.file
                if path.exists():
                    source = path.read_text(encoding="utf-8")
                    resp = self.ask_llm(
                        "You are the Debugging Agent. Fix the reported error in the given "
                        "Python file. Respond with the FULL corrected file content only, "
                        "inside a ```python fence.",
                        f"Error: {message}\n\nFile: {finding.file}\n\n```python\n{source}\n```",
                    )
                    if resp:
                        m2 = re.search(r"```python\s*(.*?)```", resp.text, re.DOTALL)
                        new_source = (m2.group(1) if m2 else resp.text).strip()
                        if new_source and new_source != source.strip():
                            path.write_text(new_source + "\n", encoding="utf-8")
                            fixes += 1
        return fixes
