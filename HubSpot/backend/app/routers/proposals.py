import uuid

from fastapi import APIRouter

from app import db
from app.models import Proposal
from app.services import proposal as proposal_svc

router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.post("/generate")
def generate(customer_id: str, messages: list[str]):
    terms = proposal_svc.extract_terms(messages)
    missing = proposal_svc.missing_information(terms)
    p = Proposal(id=f"prop_{uuid.uuid4().hex[:6]}", customer_id=customer_id, **terms)
    db.proposals[p.id] = p
    return {"proposal": p, "missing": missing, "text": proposal_svc.render(terms, customer_id)}


@router.get("/{proposal_id}")
def get(proposal_id: str):
    return db.proposals.get(proposal_id) or {"error": "not found"}
