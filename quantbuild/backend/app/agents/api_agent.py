"""API Agent — designs the REST API contract.

Generates a complete OpenAPI 3.0 specification (auth + CRUD per entity),
keeping the frontend and backend synchronized through one shared contract.
"""
from __future__ import annotations

from typing import Any

from .base import BaseAgent

JSON_TYPES = {"str": "string", "text": "string", "int": "integer", "float": "number",
              "bool": "boolean", "datetime": "string", "date": "string", "fk": "integer"}
FORMATS = {"datetime": "date-time", "date": "date"}


class APIAgent(BaseAgent):
    name = "API Design Agent"
    stage = "api_design"

    def run(self) -> dict[str, Any]:
        spec = self.ctx.specification
        self.start("Designing REST API contract")

        paths: dict[str, Any] = {}
        schemas: dict[str, Any] = {}
        endpoints: list[dict[str, str]] = []

        self._auth_paths(paths, endpoints)
        for ent in spec["entities"]:
            if ent["name"] == "User":
                self._user_paths(paths, schemas, endpoints, ent)
                continue
            self._crud_paths(paths, schemas, endpoints, ent)

        openapi = {
            "openapi": "3.0.3",
            "info": {"title": f"{spec['name']} API", "version": "1.0.0",
                     "description": spec.get("summary", "")},
            "components": {
                "securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer",
                                                   "bearerFormat": "JWT"}},
                "schemas": schemas,
            },
            "security": [{"bearerAuth": []}],
            "paths": paths,
        }
        self.ctx.api_contract = {"openapi": openapi, "endpoints": endpoints}
        self.ctx.save()
        self.done(f"API contract ready: {len(endpoints)} endpoints across "
                  f"{len(spec['entities'])} resources")
        return self.ctx.api_contract

    # ---------------------------------------------------------------- helpers
    def _entity_schema(self, ent: dict[str, Any]) -> dict[str, Any]:
        props: dict[str, Any] = {}
        required: list[str] = []
        for field in ent["fields"]:
            prop: dict[str, Any] = {"type": JSON_TYPES.get(field["type"], "string")}
            if field["type"] in FORMATS:
                prop["format"] = FORMATS[field["type"]]
            if field.get("nullable"):
                prop["nullable"] = True
            props[field["name"]] = prop
            if not field.get("nullable") and not field.get("primary_key") \
                    and "default" not in field and field["name"] != "password_hash":
                required.append(field["name"])
        return {"type": "object", "properties": props, "required": required}

    def _create_schema(self, ent: dict[str, Any]) -> dict[str, Any]:
        props: dict[str, Any] = {}
        required: list[str] = []
        for field in ent["fields"]:
            if field.get("primary_key") or field["name"] in ("created_at", "password_hash"):
                continue
            prop: dict[str, Any] = {"type": JSON_TYPES.get(field["type"], "string")}
            if field["type"] in FORMATS:
                prop["format"] = FORMATS[field["type"]]
            props[field["name"]] = prop
            if not field.get("nullable") and "default" not in field:
                required.append(field["name"])
        return {"type": "object", "properties": props, "required": required}

    def _crud_paths(self, paths: dict[str, Any], schemas: dict[str, Any],
                    endpoints: list[dict[str, str]], ent: dict[str, Any]) -> None:
        name, table = ent["name"], ent["table"]
        schemas[name] = self._entity_schema(ent)
        schemas[f"{name}Create"] = self._create_schema(ent)
        base = f"/api/{table.replace('_', '-')}"
        tag = name

        def op(method: str, summary: str, *, body: bool = False, item: bool = False) -> dict:
            operation: dict[str, Any] = {"tags": [tag], "summary": summary, "responses": {
                "200": {"description": "Success"},
                "401": {"description": "Not authenticated"},
                "403": {"description": "Forbidden"},
            }}
            if item:
                operation["parameters"] = [{
                    "name": f"{name.lower()}_id", "in": "path", "required": True,
                    "schema": {"type": "integer"}}]
                operation["responses"]["404"] = {"description": f"{name} not found"}
            if method == "post":
                operation["responses"] = {"201": {"description": "Created"},
                                          "422": {"description": "Validation error"}}
            if body:
                operation["requestBody"] = {"required": True, "content": {
                    "application/json": {"schema": {"$ref": f"#/components/schemas/{name}Create"}}}}
            return operation

        paths[base] = {
            "get": op("get", f"List {table}"),
            "post": op("post", f"Create a {name}", body=True),
        }
        paths[f"{base}/{{item_id}}"] = {
            "get": op("get", f"Get a {name}", item=True),
            "put": op("put", f"Update a {name}", body=True, item=True),
            "delete": op("delete", f"Delete a {name}", item=True),
        }
        for method, path, summary in [
            ("GET", base, f"List {table}"), ("POST", base, f"Create {name}"),
            ("GET", f"{base}/{{id}}", f"Get {name}"), ("PUT", f"{base}/{{id}}", f"Update {name}"),
            ("DELETE", f"{base}/{{id}}", f"Delete {name}"),
        ]:
            endpoints.append({"method": method, "path": path, "summary": summary,
                              "resource": name})

    def _user_paths(self, paths: dict[str, Any], schemas: dict[str, Any],
                    endpoints: list[dict[str, str]], ent: dict[str, Any]) -> None:
        schemas["User"] = self._entity_schema(ent)
        paths["/api/users/me"] = {"get": {"tags": ["User"], "summary": "Current user profile",
                                          "responses": {"200": {"description": "Success"}}}}
        paths["/api/users"] = {"get": {"tags": ["User"], "summary": "List users (admin)",
                                       "responses": {"200": {"description": "Success"}}}}
        endpoints.append({"method": "GET", "path": "/api/users/me",
                          "summary": "Current user profile", "resource": "User"})
        endpoints.append({"method": "GET", "path": "/api/users",
                          "summary": "List users (admin)", "resource": "User"})

    def _auth_paths(self, paths: dict[str, Any], endpoints: list[dict[str, str]]) -> None:
        paths["/api/auth/register"] = {"post": {
            "tags": ["Auth"], "summary": "Register a new account", "security": [],
            "requestBody": {"required": True, "content": {"application/json": {"schema": {
                "type": "object", "required": ["email", "password", "full_name"],
                "properties": {"email": {"type": "string", "format": "email"},
                               "password": {"type": "string", "minLength": 8},
                               "full_name": {"type": "string"}}}}}},
            "responses": {"201": {"description": "Registered"},
                          "409": {"description": "Email already registered"}}}}
        paths["/api/auth/login"] = {"post": {
            "tags": ["Auth"], "summary": "Log in and receive a JWT", "security": [],
            "requestBody": {"required": True, "content": {"application/json": {"schema": {
                "type": "object", "required": ["email", "password"],
                "properties": {"email": {"type": "string"},
                               "password": {"type": "string"}}}}}},
            "responses": {"200": {"description": "Authenticated"},
                          "401": {"description": "Invalid credentials"}}}}
        endpoints.append({"method": "POST", "path": "/api/auth/register",
                          "summary": "Register account", "resource": "Auth"})
        endpoints.append({"method": "POST", "path": "/api/auth/login",
                          "summary": "Login (JWT)", "resource": "Auth"})
