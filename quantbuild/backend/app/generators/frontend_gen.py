"""Frontend code generator — emits a Vite + React + TypeScript + Tailwind SPA.

Static component/page code lives as real files under
``app/templates/frontend/`` (shared with the live-preview bundle, so generated
apps and previews never drift apart).  Per-project files — package.json,
index.html, types.ts, entityConfig.ts, appInfo.ts — are generated from the
specification.

Pages are driven by a typed entity configuration: one generic, well-tested
EntityListPage renders the table, search, create/edit modal and delete
confirmation for every resource, which keeps the generated codebase small,
consistent and type-safe.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .common import OWNER_FIELD_NAMES, ts_type

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "frontend"

# Template files copied verbatim into every generated project.
_STATIC_FILES = [
    "vite.config.ts",
    "tsconfig.json",
    "tailwind.config.js",
    "postcss.config.js",
    "src/index.css",
    "src/main.tsx",
    "src/App.tsx",
    "src/api/client.ts",
    "src/auth/AuthContext.tsx",
    "src/components/Navbar.tsx",
    "src/components/ProtectedRoute.tsx",
    "src/components/FormField.tsx",
    "src/components/DataTable.tsx",
    "src/components/Spinner.tsx",
    "src/components/EmptyState.tsx",
    "src/pages/Home.tsx",
    "src/pages/Login.tsx",
    "src/pages/Register.tsx",
    "src/pages/Dashboard.tsx",
    "src/pages/Profile.tsx",
    "src/pages/Admin.tsx",
    "src/pages/EntityListPage.tsx",
]


# ---------------------------------------------------------------------------
# dynamic files
# ---------------------------------------------------------------------------

def render_package_json(spec: dict[str, Any]) -> str:
    pkg = {
        "name": spec["name"].lower().replace(" ", "-") + "-frontend",
        "private": True,
        "version": "1.0.0",
        "type": "module",
        "scripts": {"dev": "vite", "build": "tsc -b && vite build",
                    "preview": "vite preview"},
        "dependencies": {
            "react": "^18.3.1",
            "react-dom": "^18.3.1",
            "react-router-dom": "^6.28.0",
        },
        "devDependencies": {
            "@types/react": "^18.3.12",
            "@types/react-dom": "^18.3.1",
            "@vitejs/plugin-react": "^4.3.4",
            "autoprefixer": "^10.4.20",
            "postcss": "^8.4.49",
            "tailwindcss": "^3.4.16",
            "typescript": "^5.6.3",
            "vite": "^5.4.11",
        },
    }
    return json.dumps(pkg, indent=2) + "\n"


def render_index_html(spec: dict[str, Any]) -> str:
    return ('<!doctype html>\n<html lang="en">\n  <head>\n'
            '    <meta charset="UTF-8" />\n'
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
            f"    <title>{spec['name']}</title>\n"
            "  </head>\n  <body>\n"
            '    <div id="root"></div>\n'
            '    <script type="module" src="/src/main.tsx"></script>\n'
            "  </body>\n</html>\n")


def _field_input(field: dict[str, Any]) -> str:
    if field["type"] in ("int", "float"):
        return "number"
    if field["type"] == "bool":
        return "checkbox"
    if field["type"] == "text":
        return "textarea"
    if field["type"] == "datetime":
        return "datetime-local"
    if field["type"] == "date":
        return "date"
    return "text"


def entity_ui_configs(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per-entity table/form configuration (drives EntityListPage + preview)."""
    configs: list[dict[str, Any]] = []
    for ent in entities:
        if ent["name"] == "User":
            continue
        columns = [{"key": "id", "label": "ID"}]
        shown = 0
        for field in ent["fields"]:
            if shown >= 4:
                break
            if field.get("primary_key") or field["name"] == "created_at" \
                    or field["type"] in ("fk", "text"):
                continue
            columns.append({"key": field["name"],
                            "label": field["name"].replace("_", " ").title()})
            shown += 1
        fields = []
        for field in ent["fields"]:
            if field.get("primary_key") or field["name"] == "created_at":
                continue
            if field["name"] in OWNER_FIELD_NAMES and field.get("ref") == "User":
                continue  # auto-assigned from the JWT
            fields.append({
                "key": field["name"],
                "label": field["name"].replace("_", " ").title(),
                "input": "number" if field["type"] == "fk" else _field_input(field),
                "required": not field.get("nullable") and "default" not in field,
            })
        configs.append({
            "resource": ent["table"].replace("_", "-"),
            "label": ent["table"].replace("_", " ").title(),
            "columns": columns,
            "fields": fields,
        })
    return configs


_ENTITY_CONFIG_HEADER = """/** Per-entity UI configuration generated from the database schema. */

export interface EntityFieldConfig {
  key: string;
  label: string;
  input: "text" | "number" | "checkbox" | "textarea" | "datetime-local" | "date";
  required: boolean;
}

export interface EntityConfig {
  resource: string;
  label: string;
  columns: { key: string; label: string }[];
  fields: EntityFieldConfig[];
}

export const entityConfigs: EntityConfig[] ="""


def render_entity_config(entities: list[dict[str, Any]]) -> str:
    configs = entity_ui_configs(entities)
    return _ENTITY_CONFIG_HEADER + " " + json.dumps(configs, indent=2) + ";\n"


def render_app_info(spec: dict[str, Any]) -> str:
    info = {
        "name": spec["name"],
        "appType": spec.get("app_type", "Web Application"),
        "features": spec.get("features", [])[:9],
    }
    return ("/** Application metadata generated from the specification. */\n"
            "export const appInfo = " + json.dumps(info, indent=2) + " as const;\n")


def render_types(entities: list[dict[str, Any]]) -> str:
    parts = ["/** Shared entity types generated from the API contract. */\n"]
    for ent in entities:
        parts.append(f"export interface {ent['name']} {{")
        for field in ent["fields"]:
            if field["name"] == "password_hash":
                continue
            optional = "?" if field.get("nullable") else ""
            parts.append(f"  {field['name']}{optional}: {ts_type(field)};")
        parts.append("}\n")
    return "\n".join(parts)


def entity_file_map(spec: dict[str, Any]) -> dict[str, str]:
    """Full mapping of generated-frontend relative paths to contents."""
    entities = spec["entities"]
    files: dict[str, str] = {}
    # static template files
    for rel in _STATIC_FILES:
        source = TEMPLATES_DIR / rel
        files[f"frontend/{rel}"] = source.read_text(encoding="utf-8")
    # generated files
    files.update({
        "frontend/package.json": render_package_json(spec),
        "frontend/index.html": render_index_html(spec),
        "frontend/src/types.ts": render_types(entities),
        "frontend/src/entityConfig.ts": render_entity_config(entities),
        "frontend/src/appInfo.ts": render_app_info(spec),
        "frontend/README.md": f"# {spec['name']} Frontend\n\nReact + TypeScript + Tailwind SPA.\n\n"
                              "```bash\nnpm install\nnpm run dev\n```\n\n"
                              "The dev server proxies `/api` to `http://localhost:8000`.\n",
    })
    return files
