"""Long-term customer memory layer."""
from app import db


def remember(customer_id: str, key: str, value):
    db.customer_memory.setdefault(customer_id, {})[key] = value


def recall(customer_id: str) -> dict:
    return db.customer_memory.get(customer_id, {})
