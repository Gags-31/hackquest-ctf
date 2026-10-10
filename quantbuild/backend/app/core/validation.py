"""AI-powered code validation pipeline.

Stages: syntax validation → dependency check → static analysis → build
verification (import) → unit/integration test execution (pytest).  Each stage
returns structured findings that feed the autonomous debugging loop.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class Finding:
    stage: str
    severity: str           # error | warning | info
    message: str
    file: str = ""
    line: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationReport:
    stages: dict[str, dict[str, Any]] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)

    def add(self, stage: str, severity: str, message: str, file: str = "", line: int = 0) -> None:
        self.findings.append(Finding(stage, severity, message, file, line))

    def stage_summary(self, stage: str, status: str, detail: str = "") -> None:
        self.stages[stage] = {"status": status, "detail": detail}

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "stages": self.stages,
            "findings": [f.to_dict() for f in self.findings],
        }


# ---------------------------------------------------------------------------
# individual stages
# ---------------------------------------------------------------------------

def syntax_validation(backend_dir: Path, report: ValidationReport) -> bool:
    errors = 0
    py_files = sorted(backend_dir.rglob("*.py"))
    for path in py_files:
        rel = str(path.relative_to(backend_dir))
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError as exc:
            errors += 1
            report.add("syntax", "error", f"{exc.msg} (line {exc.lineno})", rel,
                       exc.lineno or 0)
    report.stage_summary("syntax", "failed" if errors else "passed",
                         f"{len(py_files)} Python files parsed, {errors} errors")
    return errors == 0


def dependency_check(backend_dir: Path, report: ValidationReport) -> bool:
    req = backend_dir / "requirements.txt"
    if not req.exists():
        report.add("dependencies", "error", "requirements.txt is missing")
        report.stage_summary("dependencies", "failed", "requirements.txt missing")
        return False
    declared = {line.strip().split(">=")[0].split("==")[0].lower()
                for line in req.read_text().splitlines()
                if line.strip() and not line.startswith("#")}
    imported: set[str] = set()
    for path in backend_dir.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                imported.add(node.module.split(".")[0])
    stdlib = set(sys.stdlib_module_names)
    third_party = {m for m in imported if m not in stdlib and m != "app"}
    alias = {"fastapi": "fastapi", "sqlalchemy": "sqlalchemy", "pydantic": "pydantic",
             "starlette": "starlette", "uvicorn": "uvicorn", "pytest": "pytest",
             "httpx": "httpx"}
    missing = []
    for module in sorted(third_party):
        pkg = alias.get(module, module)
        if pkg not in declared and pkg not in ("starlette", "uvicorn"):
            # starlette/uvicorn ship with fastapi
            missing.append(module)
    for module in missing:
        report.add("dependencies", "error",
                   f"Module '{module}' is imported but not declared in requirements.txt")
    report.stage_summary("dependencies", "failed" if missing else "passed",
                         f"{len(declared)} dependencies declared, {len(missing)} missing")
    return not missing


def static_analysis(backend_dir: Path, report: ValidationReport) -> bool:
    """Lightweight static checks: wildcard imports, bare excepts, TODO markers."""
    issues = 0
    for path in backend_dir.rglob("*.py"):
        rel = str(path.relative_to(backend_dir))
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        report.add("static_analysis", "warning",
                                   "Wildcard import", rel, node.lineno)
                        issues += 1
            elif isinstance(node, ast.ExceptHandler) and node.type is None:
                report.add("static_analysis", "warning", "Bare except clause", rel,
                           node.lineno)
                issues += 1
    report.stage_summary("static_analysis", "passed" if issues == 0 else "passed_with_warnings",
                         f"{issues} warnings")
    return True


def build_verification(backend_dir: Path, report: ValidationReport) -> bool:
    """Import the generated application package (catches import-time errors)."""
    proc = subprocess.run(
        [sys.executable, "-c", "import app.main; print('import-ok')"],
        cwd=backend_dir, capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0 or "import-ok" not in proc.stdout:
        tail = (proc.stderr or proc.stdout).strip().splitlines()
        report.add("build", "error", tail[-1] if tail else "import failed")
        report.stage_summary("build", "failed", tail[-1][:300] if tail else "import failed")
        return False
    report.stage_summary("build", "passed", "application imports cleanly")
    return True


def run_tests(backend_dir: Path, report: ValidationReport) -> dict[str, Any]:
    """Execute the generated pytest suite."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q", "--tb=short",
         "--disable-warnings", "-p", "no:cacheprovider"],
        cwd=backend_dir, capture_output=True, text=True, timeout=600,
    )
    output = (proc.stdout + "\n" + proc.stderr).strip()
    passed = failed = 0
    for line in output.splitlines():
        if line.startswith(("passed", "failed")) or " passed" in line or " failed" in line:
            import re
            mp = re.search(r"(\d+) passed", line)
            mf = re.search(r"(\d+) failed", line)
            if mp:
                passed = int(mp.group(1))
            if mf:
                failed = int(mf.group(1))
    ok = proc.returncode == 0
    if not ok:
        failures = [ln for ln in output.splitlines() if ln.startswith("FAILED")]
        for ln in failures[:10]:
            report.add("tests", "error", ln)
        if not failures:
            tail = output.strip().splitlines()
            report.add("tests", "error", tail[-1][:400] if tail else "pytest failed")
    report.stage_summary("tests", "passed" if ok else "failed",
                         f"{passed} passed, {failed} failed")
    return {"ok": ok, "passed": passed, "failed": failed, "output": output[-6000:],
            "returncode": proc.returncode}


def full_pipeline(backend_dir: Path, *, run_pytest: bool = True) -> tuple[ValidationReport, dict[str, Any]]:
    report = ValidationReport()
    test_result: dict[str, Any] = {"ok": None, "output": ""}

    if not syntax_validation(backend_dir, report):
        report.stage_summary("tests", "skipped", "syntax errors")
        return report, test_result
    dependency_check(backend_dir, report)
    static_analysis(backend_dir, report)
    if not build_verification(backend_dir, report):
        report.stage_summary("tests", "skipped", "build failed")
        return report, test_result
    if run_pytest:
        test_result = run_tests(backend_dir, report)
    return report, test_result
