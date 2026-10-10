"""UI/UX Agent — designs screens, components and navigation."""
from __future__ import annotations

from typing import Any

from .base import BaseAgent


class UIUXAgent(BaseAgent):
    name = "UI/UX Agent"
    stage = "uiux_design"

    def run(self) -> dict[str, Any]:
        spec = self.ctx.specification
        self.start("Designing application screens and component structure")

        pages: list[dict[str, Any]] = [
            {"name": "Home", "path": "/", "public": True,
             "description": f"Landing page introducing {spec['name']}",
             "components": ["Hero", "FeatureGrid", "Footer"]},
            {"name": "Register", "path": "/register", "public": True,
             "description": "Create an account", "components": ["RegisterForm"]},
            {"name": "Login", "path": "/login", "public": True,
             "description": "Authenticate and receive a JWT",
             "components": ["LoginForm"]},
            {"name": "Dashboard", "path": "/dashboard", "public": False,
             "description": "Signed-in overview with key metrics",
             "components": ["StatCards", "RecentActivity"]},
        ]
        for ent in spec["entities"]:
            if ent["name"] == "User":
                pages.append({"name": "Profile", "path": "/profile", "public": False,
                              "description": "Manage the signed-in user's profile",
                              "components": ["ProfileForm"]})
                continue
            plural = ent["table"].replace("_", " ")
            pages.append({
                "name": f"{ent['name']}List", "path": f"/{ent['table'].replace('_', '-')}",
                "public": False,
                "description": f"Browse, search and manage {plural}",
                "components": ["DataTable", "SearchBar", f"{ent['name']}Form",
                               "ConfirmDialog"],
            })
        if "Admin" in spec.get("users", []) or "Administrator" in spec.get("users", []):
            pages.append({"name": "Admin", "path": "/admin", "public": False,
                          "roles": ["Admin", "Administrator"],
                          "description": "Administrative console",
                          "components": ["UserTable", "SystemStats"]})

        design = {
            "pages": pages,
            "shared_components": ["Navbar", "ProtectedRoute", "FormField", "DataTable",
                                  "Modal", "Toast", "Spinner", "EmptyState"],
            "navigation": [p["name"] for p in pages if not p["public"] and p["name"] != "Profile"],
            "style": {"framework": "Tailwind CSS", "theme": "slate + indigo accent",
                      "layout": "responsive grid, max-w-7xl container"},
        }
        self.ctx.ui_design = design
        self.ctx.save()
        self.done(f"Designed {len(pages)} pages and {len(design['shared_components'])} "
                  "shared components")
        return design
