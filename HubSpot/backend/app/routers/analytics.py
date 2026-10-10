from fastapi import APIRouter

from app import db
from app.services import predictive, next_action, memory

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/customer/{customer_id}")
def customer360(customer_id: str, sentiment: str = "Neutral"):
    convs = [c for c in db.conversations.values() if c.customer_id == customer_id]
    mem = memory.recall(customer_id)
    return {
        "customer_id": customer_id,
        "total_conversations": len(convs),
        "memory": mem,
        "prediction": predictive.predict(customer_id, len(convs), 75000, sentiment),
        "next_actions": next_action.rank(sentiment, mem.get("last_requirement", {}).get("intent", "General"), 5, bool(mem)),
    }
