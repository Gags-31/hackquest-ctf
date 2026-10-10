"""RAG-based software knowledge system.

A lightweight, dependency-free retrieval engine (TF-IDF + cosine similarity)
over markdown knowledge documents: framework patterns, security guidelines,
coding standards and architecture patterns.  Agents call ``retrieve`` before
generating or modifying code and receive the most relevant knowledge chunks.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

from ..config import KNOWLEDGE_DIR

_TOKEN = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.\-]*")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text)]


@dataclass
class Chunk:
    source: str
    title: str
    text: str
    tokens: list[str]


class KnowledgeBase:
    """Loads markdown docs, splits them into sections, and retrieves by TF-IDF."""

    def __init__(self, directory: Path = KNOWLEDGE_DIR) -> None:
        self.chunks: list[Chunk] = []
        self._df: dict[str, int] = {}
        self._load(directory)

    # ------------------------------------------------------------------ load
    def _load(self, directory: Path) -> None:
        for path in sorted(directory.glob("*.md")) if directory.exists() else []:
            text = path.read_text(encoding="utf-8")
            sections = re.split(r"\n(?=#{1,3}\s)", text)
            for section in sections:
                title_m = re.match(r"#{1,3}\s+(.*)", section)
                title = title_m.group(1).strip() if title_m else path.stem
                self.chunks.append(Chunk(path.name, title, section.strip(),
                                         tokenize(section)))
        self._df = {}
        for chunk in self.chunks:
            for tok in set(chunk.tokens):
                self._df[tok] = self._df.get(tok, 0) + 1

    # --------------------------------------------------------------- retrieve
    def retrieve(self, query: str, top_k: int = 3) -> list[Chunk]:
        if not self.chunks:
            return []
        n = len(self.chunks)
        q_tokens = tokenize(query)
        q_tf: dict[str, float] = {}
        for tok in q_tokens:
            q_tf[tok] = q_tf.get(tok, 0.0) + 1.0

        def idf(tok: str) -> float:
            return math.log((1 + n) / (1 + self._df.get(tok, 0))) + 1.0

        q_vec = {t: tf * idf(t) for t, tf in q_tf.items()}
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0

        scored: list[tuple[float, Chunk]] = []
        for chunk in self.chunks:
            d_tf: dict[str, float] = {}
            for tok in chunk.tokens:
                d_tf[tok] = d_tf.get(tok, 0.0) + 1.0
            d_vec = {t: tf * idf(t) for t, tf in d_tf.items() if t in q_vec}
            if not d_vec:
                continue
            dot = sum(q_vec[t] * d_vec[t] for t in d_vec)
            d_norm = math.sqrt(sum(v * v for v in d_tf.values() if True)) or 1.0
            score = dot / (q_norm * d_norm)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda sc: -sc[0])
        return [c for _, c in scored[:top_k]]

    def context_for(self, query: str, top_k: int = 3, max_chars: int = 2400) -> str:
        """Return a formatted RAG context block for LLM prompts."""
        chunks = self.retrieve(query, top_k)
        parts: list[str] = []
        total = 0
        for chunk in chunks:
            block = f"### [{chunk.source}] {chunk.title}\n{chunk.text}"
            if total + len(block) > max_chars:
                break
            parts.append(block)
            total += len(block)
        return "\n\n".join(parts)


knowledge_base = KnowledgeBase()
