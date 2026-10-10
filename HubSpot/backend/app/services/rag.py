"""RAG layer: TF-IDF-ish retrieval over customer memory + CRM records."""
import math
import re
from collections import Counter

_STORE: list[dict] = []


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def index(doc_id: str, text: str):
    _STORE.append({"id": doc_id, "text": text, "vec": Counter(_tokens(text))})


def search(query: str, k: int = 3) -> list[dict]:
    qv = Counter(_tokens(query))
    if not qv:
        return []

    def cosine(a, b):
        keys = set(a) | set(b)
        dot = sum(a[x] * b[x] for x in keys)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    scored = sorted(_STORE, key=lambda d: cosine(qv, d["vec"]), reverse=True)
    return [{"id": d["id"], "text": d["text"]} for d in scored[:k] if cosine(qv, d["vec"]) > 0]


def answer(query: str) -> dict:
    hits = search(query)
    if not hits:
        return {"answer": "No relevant CRM data found.", "sources": []}
    return {"answer": f"Based on your CRM data: {hits[0]['text'][:300]}", "sources": hits}
