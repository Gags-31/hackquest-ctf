"""Base class shared by all QuantBuild agents.

Every agent:
* reads and writes the Central Project Context,
* emits lifecycle events over the event bus (for live UI streaming),
* optionally consults the RAG knowledge base,
* uses the LLM when configured, otherwise deterministic heuristics.
"""
from __future__ import annotations

from typing import Any

from ..core.context import ProjectContext
from ..core.llm import llm_client, LLMResponse
from ..core.rag import knowledge_base


class BaseAgent:
    name: str = "Agent"
    stage: str = "stage"

    def __init__(self, ctx: ProjectContext) -> None:
        self.ctx = ctx

    # ------------------------------------------------------------- lifecycle
    def start(self, message: str) -> None:
        self.ctx.emit(self.name, self.stage, "started", message)

    def think(self, message: str, detail: dict[str, Any] | None = None) -> None:
        self.ctx.emit(self.name, self.stage, "thinking", message, detail)

    def done(self, message: str, detail: dict[str, Any] | None = None) -> None:
        self.ctx.emit(self.name, self.stage, "finished", message, detail)

    def fail(self, message: str, detail: dict[str, Any] | None = None) -> None:
        self.ctx.emit(self.name, self.stage, "failed", message, detail)

    # ---------------------------------------------------------------- helpers
    @property
    def llm_online(self) -> bool:
        return llm_client.online

    def ask_llm(self, system: str, user: str, *, json_mode: bool = False) -> LLMResponse | None:
        """Ask the configured LLM; None when offline so callers fall back."""
        self.think(f"Consulting LLM ({llm_client.provider})" if llm_client.online
                   else "Offline mode — using heuristic reasoning")
        return llm_client.try_chat(system, user, json_mode=json_mode)

    def rag(self, query: str, top_k: int = 3) -> str:
        """Retrieve relevant knowledge-base context for a task."""
        return knowledge_base.context_for(query, top_k=top_k)

    def run(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError
