"""RAG knowledge-base retrieval tests."""
from app.core.rag import knowledge_base


def test_knowledge_base_loaded():
    assert len(knowledge_base.chunks) > 10


def test_retrieves_security_knowledge():
    chunks = knowledge_base.retrieve("JWT password hashing rate limiting", top_k=3)
    assert chunks
    assert any("security" in c.source.lower() for c in chunks)


def test_retrieves_react_knowledge():
    chunks = knowledge_base.retrieve("react router auth context forms components", top_k=3)
    assert chunks
    assert any("react" in c.source.lower() for c in chunks)


def test_context_block_is_bounded():
    ctx = knowledge_base.context_for("database indexes", top_k=5, max_chars=1000)
    assert len(ctx) <= 2400
