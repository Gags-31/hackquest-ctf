"""Frontend Agent — generates the React + TypeScript + Tailwind SPA."""
from __future__ import annotations

from .base import BaseAgent
from ..generators import frontend_gen


class FrontendAgent(BaseAgent):
    name = "Frontend Agent"
    stage = "frontend_generation"

    def run(self) -> list[str]:
        spec = self.ctx.specification
        self.start(f"Generating React frontend for {spec['name']}")
        self.rag("react project structure routing auth context forms", top_k=2)

        files = frontend_gen.entity_file_map(spec)
        for path, content in files.items():
            self.ctx.write_generated_file(path, content)

        self.ctx.dependencies["frontend"] = ["react", "react-dom", "react-router-dom",
                                             "vite", "typescript", "tailwindcss"]
        self.ctx.save()
        pages = len(self.ctx.ui_design.get("pages", []))
        self.done(f"Frontend generated: {len(files)} files, {pages} pages, "
                  f"{len(spec['entities']) - 1} entity screens")
        return list(files)
