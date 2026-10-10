"""Pipeline event bus.

Agents emit events while they work; the WebSocket layer forwards them to the
UI so users can watch the multi-agent pipeline run in real time.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class PipelineEvent:
    project_id: str
    agent: str            # e.g. "Requirement Agent"
    stage: str            # e.g. "requirement_analysis"
    status: str           # started | thinking | finished | failed | info
    message: str
    detail: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventBus:
    """Fan-out pub/sub; one asyncio.Queue per subscriber."""

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue]] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}

    def subscribe(self, project_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subscribers.setdefault(project_id, set()).add(queue)
        return queue

    def unsubscribe(self, project_id: str, queue: asyncio.Queue) -> None:
        subs = self._subscribers.get(project_id)
        if subs:
            subs.discard(queue)

    def emit(self, event: PipelineEvent) -> None:
        payload = event.to_dict()
        self._history.setdefault(event.project_id, []).append(payload)
        self._history[event.project_id] = self._history[event.project_id][-500:]
        for queue in self._subscribers.get(event.project_id, set()):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:  # pragma: no cover - defensive
                pass

    def history(self, project_id: str) -> list[dict[str, Any]]:
        return list(self._history.get(project_id, []))


bus = EventBus()
