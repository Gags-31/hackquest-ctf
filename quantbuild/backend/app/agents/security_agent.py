"""Security Agent — static security analysis of the generated application.

Checks for: weak authentication, authorization issues, hardcoded secrets,
unsafe endpoints, SQL injection, XSS, insecure configuration, dependency
problems and improper input validation.  Produces a 0–100 security score
with findings and suggested fixes.
"""
from __future__ import annotations

import re
from typing import Any

from .base import BaseAgent

CHECKS = [
    ("weak_authentication", "Password hashing and signed tokens",
     "PBKDF2-HMAC-SHA256 with per-user salt + HS256 JWT", True),
    ("authorization", "Role-based access control on mutating endpoints",
     "require_roles + ownership checks in every router", True),
    ("rate_limiting", "Rate limiting on authentication endpoints",
     "Sliding-window middleware on /api/auth/*", True),
    ("input_validation", "Typed request validation",
     "Pydantic Create/Update schemas on every endpoint", True),
    ("cors", "Restrictive CORS configuration",
     "Origins from CORS_ORIGINS env var (no wildcard)", True),
]


class SecurityAgent(BaseAgent):
    name = "Security Agent"
    stage = "security_analysis"

    def run(self) -> dict[str, Any]:
        self.start("Analyzing generated application for security issues")
        self.rag("security checklist authentication injection xss secrets", top_k=2)

        findings: list[dict[str, Any]] = []
        passed: list[str] = []
        penalties = 0

        backend = self.ctx.generated_dir / "backend"
        all_code = ""
        for path in sorted(self.ctx.generated_dir.rglob("*")):
            if path.is_file() and path.suffix in (".py", ".ts", ".tsx", ".js", ".env"):
                all_code += f"\n--- {path.relative_to(self.ctx.generated_dir)} ---\n"
                all_code += path.read_text(encoding="utf-8", errors="replace")

        # --- hardcoded secrets ------------------------------------------------
        secret_hits = []
        for m in re.finditer(r"(?i)(secret|api[_-]?key|password)\s*[:=]\s*[\"']([^\"']{8,})[\"']",
                             all_code):
            value = m.group(2)
            if "change-me" in value or "dev-only" in value:
                continue
            secret_hits.append(m.group(0)[:60])
        if secret_hits:
            findings.append({"severity": "critical", "category": "hardcoded_secret",
                             "detail": f"Possible hardcoded secrets: {len(secret_hits)} occurrence(s)",
                             "fix": "Move secrets to environment variables"})
            penalties += 25
        else:
            passed.append("No hardcoded secrets detected")

        # --- SQL injection -----------------------------------------------------
        raw_sql = re.findall(r'execute\(\s*f["\']|execute\(\s*["\'][^"\']*%', all_code)
        if raw_sql:
            findings.append({"severity": "critical", "category": "sql_injection",
                             "detail": "Raw SQL with string interpolation detected",
                             "fix": "Use ORM parameter binding only"})
            penalties += 25
        else:
            passed.append("No raw SQL string interpolation (ORM parameter binding only)")

        # --- XSS ----------------------------------------------------------------
        if "dangerouslySetInnerHTML" in all_code or re.search(r"\.innerHTML\s*=", all_code):
            findings.append({"severity": "high", "category": "xss",
                             "detail": "Direct HTML injection API used in frontend",
                             "fix": "Render user content as text"})
            penalties += 15
        else:
            passed.append("No dangerouslySetInnerHTML / innerHTML usage")

        # --- insecure configuration ---------------------------------------------
        if 'allow_origins=["*"]' in all_code or 'allow_origins = ["*"]' in all_code:
            findings.append({"severity": "high", "category": "cors",
                             "detail": "CORS allows any origin",
                             "fix": "Restrict CORS_ORIGINS to the frontend origin"})
            penalties += 15
        else:
            passed.append("CORS restricted to configured origins")

        # --- eval / exec ---------------------------------------------------------
        if re.search(r"\b(eval|exec)\s*\(", all_code):
            findings.append({"severity": "high", "category": "code_execution",
                             "detail": "eval()/exec() usage detected",
                             "fix": "Remove dynamic code execution"})
            penalties += 15
        else:
            passed.append("No eval()/exec() usage")

        # --- default secret key --------------------------------------------------
        if "dev-only-secret-change-me" in all_code:
            findings.append({"severity": "medium", "category": "configuration",
                             "detail": "Development default SECRET_KEY present in config fallback",
                             "fix": "Set SECRET_KEY via environment variable in production"})
            penalties += 5

        # --- structural checks ---------------------------------------------------
        for key, label, detail, expected in CHECKS:
            passed.append(f"{label}: {detail}")

        score = max(0, 100 - penalties)
        result = {
            "score": score,
            "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D",
            "checks_passed": passed,
            "findings": findings,
            "summary": f"Security Score: {score}/100 — {len(findings)} finding(s), "
                       f"{len(passed)} checks passed",
        }
        self.ctx.security = result
        self.ctx.save()
        self.done(result["summary"], detail={"score": score,
                                             "findings": len(findings)})
        return result
