"""LLM provider abstraction.

Supports OpenAI-compatible APIs, Anthropic, and Ollama.  When no provider is
configured the client runs in *offline* mode and agents fall back to
deterministic heuristic behaviour, so the full pipeline always works.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

from ..config import settings


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    usage: dict[str, Any] = field(default_factory=dict)

    def json(self) -> Any:
        """Parse JSON from the response, tolerating markdown fences."""
        text = self.text.strip()
        fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if fence:
            text = fence.group(1).strip()
        # locate the first JSON object/array if surrounded by prose
        if not text.startswith(("{", "[")):
            m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
            if m:
                text = m.group(1)
        return json.loads(text)


class LLMClient:
    """Unified chat-completion client with offline fallback."""

    def __init__(self) -> None:
        self.provider = settings.resolved_provider()
        self.model = settings.default_model()

    # ------------------------------------------------------------------ API
    @property
    def online(self) -> bool:
        return self.provider != "offline"

    def chat(self, system: str, user: str, *, json_mode: bool = False,
             temperature: float | None = None) -> LLMResponse:
        """Send a chat request to the configured provider."""
        temp = settings.llm_temperature if temperature is None else temperature
        if self.provider == "openai":
            return self._openai(system, user, json_mode=json_mode, temperature=temp)
        if self.provider == "anthropic":
            return self._anthropic(system, user, temperature=temp)
        if self.provider == "ollama":
            return self._ollama(system, user, json_mode=json_mode, temperature=temp)
        raise RuntimeError("LLM client is in offline mode")

    def try_chat(self, system: str, user: str, *, json_mode: bool = False) -> LLMResponse | None:
        """Chat that never raises — returns None when offline or on failure."""
        if not self.online:
            return None
        try:
            return self.chat(system, user, json_mode=json_mode)
        except Exception:
            return None

    # ------------------------------------------------------------- providers
    def _openai(self, system: str, user: str, *, json_mode: bool, temperature: float) -> LLMResponse:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": settings.llm_max_tokens,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        resp = httpx.post(
            f"{settings.openai_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json=body,
            timeout=settings.llm_timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return LLMResponse(
            text=data["choices"][0]["message"]["content"],
            provider="openai",
            model=self.model,
            usage=data.get("usage", {}),
        )

    def _anthropic(self, system: str, user: str, *, temperature: float) -> LLMResponse:
        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": settings.llm_max_tokens,
                "temperature": temperature,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=settings.llm_timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        text = "".join(b.get("text", "") for b in data.get("content", []))
        return LLMResponse(text=text, provider="anthropic", model=self.model,
                           usage=data.get("usage", {}))

    def _ollama(self, system: str, user: str, *, json_mode: bool, temperature: float) -> LLMResponse:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if json_mode:
            body["format"] = "json"
        resp = httpx.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/chat",
            json=body,
            timeout=settings.llm_timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return LLMResponse(
            text=data.get("message", {}).get("content", ""),
            provider="ollama",
            model=self.model,
            usage={},
        )


# Shared client
llm_client = LLMClient()
