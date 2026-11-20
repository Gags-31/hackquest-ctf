"""Audit trail helper."""
from sqlalchemy.orm import Session

from .models import AuditLog


def record(db: Session, actor_type: str, actor_id: int, action: str, detail: str = "") -> None:
    db.add(AuditLog(actor_type=actor_type, actor_id=int(actor_id),
                    action=action, detail=detail[:2000]))
    db.flush()
