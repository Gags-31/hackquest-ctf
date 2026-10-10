"""QuantBuild configuration.

QuantBuild works out of the box in *offline* mode (deterministic, heuristic
agents that need no external services).  To unlock the full AI experience set
one of the supported LLM providers through environment variables:

    LLM_PROVIDER=openai   OPENAI_API_KEY=...  [OPENAI_BASE_URL] [LLM_MODEL]
    LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=... [LLM_MODEL]
    LLM_PROVIDER=ollama   [OLLAMA_BASE_URL] [LLM_MODEL]
    LLM_PROVIDER=offline  (default when nothing is configured)
"""
from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
ROOT_DIR = BASE_DIR.parent                                  # quantbuild/
WORKSPACE_DIR = ROOT_DIR / "workspace"                      # generated projects
KNOWLEDGE_DIR = BASE_DIR / "app" / "knowledge"              # RAG knowledge base


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT_DIR / ".env"), extra="ignore")

    # LLM provider: openai | anthropic | ollama | offline (auto-detected)
    llm_provider: str = os.getenv("LLM_PROVIDER", "auto")
    llm_model: str = os.getenv("LLM_MODEL", "")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    llm_timeout: float = float(os.getenv("LLM_TIMEOUT", "120"))

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Debugging loop
    max_debug_iterations: int = int(os.getenv("MAX_DEBUG_ITERATIONS", "3"))

    # Sandbox preview port range
    preview_port_start: int = int(os.getenv("PREVIEW_PORT_START", "9100"))
    preview_port_end: int = int(os.getenv("PREVIEW_PORT_END", "9199"))

    def resolved_provider(self) -> str:
        """Auto-detect the LLM provider from the environment."""
        if self.llm_provider and self.llm_provider != "auto":
            return self.llm_provider
        if self.openai_api_key:
            return "openai"
        if self.anthropic_api_key:
            return "anthropic"
        return "offline"

    def default_model(self) -> str:
        if self.llm_model:
            return self.llm_model
        provider = self.resolved_provider()
        return {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-sonnet-4-5",
            "ollama": "llama3.1",
        }.get(provider, "offline-heuristics")


settings = Settings()

WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
