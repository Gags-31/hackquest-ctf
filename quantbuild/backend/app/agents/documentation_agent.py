"""Documentation Agent — generates technical documentation from the context."""
from __future__ import annotations

from .base import BaseAgent
from ..generators import docs_gen


class DocumentationAgent(BaseAgent):
    name = "Documentation Agent"
    stage = "documentation"

    def run(self) -> dict[str, str]:
        spec = self.ctx.specification
        self.start("Generating technical documentation")

        docs = {
            "README.md": docs_gen.render_readme(spec, self.ctx.tech_stack),
            "docs/ARCHITECTURE.md": docs_gen.render_architecture_doc(spec, self.ctx.architecture),
            "docs/API.md": docs_gen.render_api_doc(spec, self.ctx.api_contract),
            "docs/DATABASE.md": docs_gen.render_database_doc(spec, self.ctx.database_schema),
            "docs/DEPLOYMENT.md": docs_gen.render_deployment_doc(spec),
            ".env.example": docs_gen.render_env_example(spec),
            "openapi.json": __import__("json").dumps(
                self.ctx.api_contract.get("openapi", {}), indent=2),
        }
        for path, content in docs.items():
            self.ctx.write_generated_file(path, content)

        self.ctx.documentation = docs
        self.ctx.save()
        self.done(f"Documentation generated: {len(docs)} documents")
        return docs
