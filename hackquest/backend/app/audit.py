"""Append-only audit log. No update or delete helpers are exposed."""
from fastapi import Request
from sqlalchemy.orm import Session

from .models import AuditLog


def record(db: Session, actor: str, action: str, target: str = "",
           detail: str = "", request: Request | None = None) -> AuditLog:
    ip = ""
    if request is not None:
        ip = request.client.host if request.client else ""
    entry = AuditLog(actor=actor, action=action, target=target,
                     detail=detail, ip=ip)
    db.add(entry)
    db.commit()
    return entry


def recent(db: Session, limit: int = 200) -> list[AuditLog]:
    return db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()