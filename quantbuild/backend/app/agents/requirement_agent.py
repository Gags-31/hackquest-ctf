"""Requirement Agent — analyzes natural-language requirements.

Produces the structured project specification (application type, users,
features, entities, security needs) that seeds the Central Project Context.
"""
from __future__ import annotations

import json
from typing import Any

from .base import BaseAgent
from ..core import nlp


SPEC_SYSTEM_PROMPT = """You are the Requirement Agent of an AI software-engineering platform.
Analyze the user's natural-language application requirement and output ONLY a
JSON object with this exact shape:
{
  "name": "short product name",
  "app_type": "e.g. E-Commerce Platform",
  "summary": "one paragraph summary",
  "users": ["role1", "role2"],
  "features": ["feature1", "feature2"],
  "entities": [
    {"name": "PascalCaseName", "description": "...",
     "fields": [{"name": "field_name", "type": "str|text|int|float|bool|datetime|date|fk",
                  "primary_key": false, "unique": false, "nullable": false,
                  "ref": "OtherEntity (only for fk)"}]}
  ],
  "security": {"authentication": "JWT (email/password)",
               "authorization": "Role-Based Access Control", "roles": ["..."]}
}
Rules: every entity has an integer primary key "id"; use "fk" fields for
relationships; always include a User entity with email + password_hash fields;
extract ALL roles, features and entities implied by the requirement."""


class RequirementAgent(BaseAgent):
    name = "Requirement Agent"
    stage = "requirement_analysis"

    def run(self) -> dict[str, Any]:
        self.start("Analyzing natural-language requirement")
        spec: dict[str, Any] | None = None

        if self.llm_online:
            resp = self.ask_llm(
                SPEC_SYSTEM_PROMPT,
                f"Application requirement:\n\n{self.ctx.requirement}",
                json_mode=True,
            )
            if resp is not None:
                try:
                    spec = resp.json()
                    self.think("LLM produced a structured specification")
                except Exception as exc:
                    self.think(f"LLM output was not valid JSON ({exc}); falling back to heuristics")
                    spec = None

        if spec is None:
            preferred = self.ctx.name if self.ctx.name and self.ctx.name != "Untitled App" else None
            spec = nlp.analyze_requirement(self.ctx.requirement, name=preferred)

        self._normalize(spec)
        self.ctx.specification = spec
        self.ctx.save()
        self.done(
            f"Identified {spec['app_type']} with {len(spec['entities'])} entities, "
            f"{len(spec['features'])} features and roles {', '.join(spec['users'])}",
            detail={"entities": [e['name'] for e in spec['entities']],
                    "features": spec['features'], "users": spec['users']},
        )
        return spec

    # ------------------------------------------------------------------ utils
    def _normalize(self, spec: dict[str, Any]) -> None:
        """Guarantee structural sanity regardless of the source (LLM/heuristic)."""
        spec.setdefault("name", "GeneratedApp")
        spec.setdefault("app_type", "Web Application")
        spec.setdefault("summary", self.ctx.requirement.strip())
        spec.setdefault("users", ["User", "Admin"])
        spec.setdefault("features", [])
        spec.setdefault("security", {
            "authentication": "JWT (email/password)",
            "authorization": "Role-Based Access Control",
            "roles": spec["users"],
        })
        entities = spec.get("entities") or []
        names = {e.get("name") for e in entities}
        if "User" not in names:
            entities.insert(0, {
                "name": "User", "description": "Registered application user",
                "fields": [
                    {"name": "id", "type": "int", "primary_key": True},
                    {"name": "email", "type": "str", "unique": True},
                    {"name": "password_hash", "type": "str"},
                    {"name": "full_name", "type": "str"},
                    {"name": "role", "type": "str", "default": "user"},
                    {"name": "is_active", "type": "bool", "default": True},
                    {"name": "created_at", "type": "datetime"},
                ],
            })
        for ent in entities:
            ent.setdefault("description", f"{ent['name']} entity")
            ent["table"] = nlp.to_table_name(ent["name"])
            fields = ent.setdefault("fields", [])
            if not any(fld.get("primary_key") for fld in fields):
                fields.insert(0, {"name": "id", "type": "int", "primary_key": True})
            for fld in fields:
                fld.setdefault("type", "str")
                if fld.get("type") == "fk" and fld.get("ref"):
                    fld["ref_table"] = nlp.to_table_name(fld["ref"])
        spec["entities"] = nlp.repair_references(entities)


def spec_to_pretty_json(spec: dict[str, Any]) -> str:
    return json.dumps(spec, indent=2)
