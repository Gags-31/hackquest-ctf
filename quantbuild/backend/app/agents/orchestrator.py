"""Project Manager Agent — the central orchestrator.

Coordinates the complete development pipeline:

    Requirement → Architecture → Database → API → UI/UX → Frontend + Backend
    → Testing → Debugging loop → Security → Documentation → Deployment

It also drives natural-language *modification*: the Requirement Agent re-reads
the instruction, the Impact Analysis engine computes affected components, the
architecture/database/API are updated, code is regenerated, and the validation
loop runs again.
"""
from __future__ import annotations

from typing import Any

from .api_agent import APIAgent
from .architecture_agent import ArchitectureAgent
from .backend_agent import BackendAgent
from .base import BaseAgent
from .database_agent import DatabaseAgent
from .debugging_agent import DebuggingAgent
from .deployment_agent import DeploymentAgent
from .documentation_agent import DocumentationAgent
from .frontend_agent import FrontendAgent
from .requirement_agent import RequirementAgent
from .security_agent import SecurityAgent
from .testing_agent import TestingAgent
from .uiux_agent import UIUXAgent
from ..core import nlp
from ..core.context import ProjectContext


class ProjectManagerAgent(BaseAgent):
    name = "Project Manager Agent"
    stage = "orchestration"

    # ---------------------------------------------------------------- pipeline
    def run_full_pipeline(self) -> ProjectContext:
        ctx = self.ctx
        ctx.status = "generating"
        ctx.save()
        self.start("Coordinating the multi-agent development pipeline")
        try:
            RequirementAgent(ctx).run()
            ArchitectureAgent(ctx).run()
            DatabaseAgent(ctx).run()
            APIAgent(ctx).run()
            UIUXAgent(ctx).run()
            FrontendAgent(ctx).run()
            BackendAgent(ctx).run()
            TestingAgent(ctx).run()            # generate + execute tests
            DebuggingAgent(ctx).run()          # validation + repair loop
            SecurityAgent(ctx).run()
            DocumentationAgent(ctx).run()
            DeploymentAgent(ctx).run()
            ctx.status = "generated"
            ctx.save()
            self.done("Pipeline complete — application is deployment-ready")
        except Exception as exc:  # pragma: no cover - defensive
            ctx.status = "failed"
            ctx.known_issues.append(f"Pipeline failure: {exc}")
            ctx.save()
            self.fail(f"Pipeline failed: {exc}")
            raise
        return ctx

    # ------------------------------------------------------------- modification
    def run_modification(self, instruction: str) -> dict[str, Any]:
        ctx = self.ctx
        ctx.status = "modifying"
        ctx.save()
        self.start(f"Processing modification request: “{instruction}”")

        spec = ctx.specification
        mod = nlp.analyze_modification(instruction, spec)
        impact = self._impact_analysis(mod, spec)
        ctx.impact_analyses.append(impact)

        self.think("Impact analysis complete", detail=impact["affected"])

        # --- apply to the specification ---------------------------------------
        if mod["auth_change"]:
            provider = mod["auth_change"]["provider"]
            spec.setdefault("security", {})["authentication"] = \
                f"OAuth 2.0 ({provider.capitalize()}) + JWT session"
            spec["security"]["oauth_provider"] = provider
            self.think(f"Authentication switched to OAuth ({provider})")

        for ename in mod["removed_entities"]:
            spec["entities"] = [e for e in spec["entities"] if e["name"] != ename]
            spec["features"] = [f for f in spec["features"]
                                if ename.lower() not in f.lower()]

        for ename in mod["new_entities"]:
            if ename in nlp.ENTITY_CATALOG:
                schema = nlp.build_entity_schema([ename])[0]
            else:
                schema = {
                    "name": ename,
                    "table": nlp.to_table_name(ename),
                    "description": f"{ename} (added by user modification)",
                    "fields": nlp.generic_entity_fields(ename),
                }
            if ename not in {e["name"] for e in spec["entities"]}:
                spec["entities"].append(schema)
        for feat in mod["new_features"]:
            if feat not in spec["features"]:
                spec["features"].append(feat)

        ctx.specification = spec
        ctx.modifications.append({"instruction": instruction, "analysis": mod,
                                  "affected": impact["affected"]})
        ctx.save()

        # --- regenerate everything derived from the spec -----------------------
        ArchitectureAgent(ctx).run()
        DatabaseAgent(ctx).run()
        APIAgent(ctx).run()
        UIUXAgent(ctx).run()
        FrontendAgent(ctx).run()
        BackendAgent(ctx).run()
        TestingAgent(ctx).run()
        DebuggingAgent(ctx).run()
        SecurityAgent(ctx).run()
        DocumentationAgent(ctx).run()
        DeploymentAgent(ctx).run()

        ctx.status = "generated"
        ctx.save()
        self.done("Modification applied and re-validated")
        return {"analysis": mod, "impact": impact, "entities": len(spec["entities"])}

    # --------------------------------------------------------------- impact
    def _impact_analysis(self, mod: dict[str, Any],
                         spec: dict[str, Any]) -> dict[str, Any]:
        self.think("Running AI impact analysis across architecture layers")
        affected = mod.get("affected", {})
        components = {
            "database": affected.get("database", []),
            "backend": affected.get("backend", []),
            "frontend": affected.get("frontend", []),
            "testing": affected.get("testing", []),
            "documentation": ["README", "API reference", "database docs"],
        }
        risk = "low"
        if mod.get("auth_change") or mod["intent"] == "remove":
            risk = "high"
        elif len(mod.get("new_entities", [])) > 1:
            risk = "medium"
        return {"change_request": mod["instruction"], "intent": mod["intent"],
                "affected": components, "risk": risk,
                "safe": True}
