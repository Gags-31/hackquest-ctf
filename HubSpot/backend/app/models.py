from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class Customer(BaseModel):
    id: str
    name: str
    contact: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Conversation(BaseModel):
    id: str
    customer_id: str
    messages: List[dict] = []
    summary: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Requirement(BaseModel):
    quantity: Optional[str] = None
    budget: Optional[str] = None
    delivery: Optional[str] = None
    intent: Optional[str] = None
    priority: Optional[str] = None


class Proposal(BaseModel):
    id: str
    customer_id: str
    product: Optional[str] = None
    quantity: Optional[str] = None
    price: Optional[str] = None
    delivery: Optional[str] = None
    payment: Optional[str] = None
    warranty: Optional[str] = None
    status: str = "draft"
