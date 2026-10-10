"""Deployment Agent — generates deployment-ready configuration."""
from __future__ import annotations

from .base import BaseAgent
from ..generators import deploy_gen


class DeploymentAgent(BaseAgent):
    name = "Deployment Agent"
    stage = "deployment"

    def run(self) -> dict[str, str]:
        spec = self.ctx.specification
        self.start("Generating deployment configuration")

        files = deploy_gen.deployment_file_map(spec)
        for path, content in files.items():
            self.ctx.write_generated_file(path, content)

        self.ctx.deployment = {
            "files": list(files),
            "targets": ["Docker Compose (local/vps)", "GitHub Actions CI"],
            "status": "deployment-ready",
        }
        self.ctx.save()
        self.done(f"Deployment configuration generated: {len(files)} files "
                  "(Dockerfiles, compose, CI/CD)")
        return files
