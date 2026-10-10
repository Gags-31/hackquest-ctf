import uuid

from fastapi import APIRouter

from app import db
from app.models import Customer

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("/")
def create(name: str, contact: str | None = None):
    c = Customer(id=f"Consumer_{uuid.uuid4().hex[:6]}", name=name, contact=contact)
    db.customers[c.id] = c
    return c


@router.get("/")
def list_all():
    return list(db.customers.values())


@router.get("/{customer_id}")
def get(customer_id: str):
    return db.customers.get(customer_id) or {"error": "not found"}
