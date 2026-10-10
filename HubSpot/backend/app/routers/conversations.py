import uuid

from fastapi import APIRouter

from app import db
from app.models import Conversation
from app.services import nlp, memory, rag

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/")
def create(customer_id: str, messages: list[str]):
    conv = Conversation(id=f"conv_{uuid.uuid4().hex[:6]}", customer_id=customer_id, messages=[{"role": "user", "text": m} for m in messages])
    conv.summary = nlp.summarize(messages)
    db.conversations[conv.id] = conv
    joined = " ".join(messages)
    entities = nlp.extract_entities(joined)
    memory.remember(customer_id, "last_requirement", entities)
    memory.remember(customer_id, "last_sentiment", nlp.sentiment(joined))
    rag.index(f"{customer_id}-{conv.id}", joined)
    return {"conversation": conv, "entities": entities, "sentiment": nlp.sentiment(joined)}


@router.get("/{conversation_id}")
def get(conversation_id: str):
    return db.conversations.get(conversation_id) or {"error": "not found"}
