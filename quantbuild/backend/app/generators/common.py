"""Shared helpers used by the backend / frontend / test generators."""
from __future__ import annotations

from typing import Any

# Field names that denote "the acting user owns this row" and are therefore
# auto-assigned from the JWT rather than accepted from the request body.
OWNER_FIELD_NAMES = {
    "user_id", "owner_id", "author_id", "organizer_id", "host_id", "employer_id",
    "instructor_id", "created_by", "guest_id", "sender_id", "agent_id",
    "applicant_id", "student_id",
}

ADMIN_ROLES = {"admin", "administrator"}


def owner_field(ent: dict[str, Any]) -> dict[str, Any] | None:
    """Return the FK field that ties this entity to the acting user, if any."""
    for field in ent.get("fields", []):
        if field.get("type") == "fk" and field.get("ref") == "User" \
                and field["name"] in OWNER_FIELD_NAMES:
            return field
    return None


def fk_fields(ent: dict[str, Any]) -> list[dict[str, Any]]:
    return [f for f in ent.get("fields", []) if f.get("type") == "fk"]


def topo_sort(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Order entities so FK dependencies are created before their dependents."""
    by_name = {e["name"]: e for e in entities}
    ordered: list[dict[str, Any]] = []
    placed: set[str] = set()
    remaining = list(entities)
    guard = 0
    while remaining and guard < 1000:
        guard += 1
        for ent in list(remaining):
            deps = {f["ref"] for f in fk_fields(ent)
                    if f.get("ref") in by_name and f["ref"] != ent["name"]}
            if deps <= placed:
                ordered.append(ent)
                placed.add(ent["name"])
                remaining.remove(ent)
    ordered.extend(remaining)  # cycles: append as-is
    return ordered


def sample_value(field: dict[str, Any], ent_name: str, index: int,
                 fk_lookup: dict[str, int]) -> Any:
    """Produce a plausible sample value for a field (tests and seed data)."""
    name, ftype = field["name"], field["type"]
    if field.get("primary_key") or name == "created_at":
        return None
    if ftype == "fk":
        return fk_lookup.get(field.get("ref", ""), 1)
    if name in OWNER_FIELD_NAMES and field.get("ref") == "User":
        return fk_lookup.get("User", 1)
    if name == "email":
        return f"user{index}@example.com"
    if name in ("password", "password_hash"):
        return "Str0ngPass!"
    if name in ("sku",):
        return f"SKU-{ent_name[:3].upper()}-{index:04d}"
    if name in ("name", "title", "full_name", "plan_name", "line1"):
        if name == "line1":
            return f"{10 + index} Example Street"
        return f"Sample {ent_name} {index}"
    if name in ("city", "state", "country"):
        return {"city": "Metropolis", "state": "State", "country": "Country"}[name]
    if name in ("postal_code",):
        return f"1000{index}"
    if name in ("phone",):
        return f"+1-555-010{index}"
    if name in ("tracking_number", "transaction_ref"):
        return f"TRK-{index:06d}"
    if name in ("image_url", "resume_url"):
        return f"https://example.com/{name.replace('_', '-')}-{index}.png"
    if name in ("location", "address"):
        return f"{index} Demo Avenue, Metropolis"
    if name in ("specialization",):
        return "General Medicine"
    if name in ("cuisine",):
        return "Italian"
    if name in ("carrier",):
        return "DHL"
    if name in ("method",):
        return "card"
    if name in ("seat",):
        return f"A{index}"
    if name in ("currency",):
        return "USD"
    if name in ("gender",):
        return "unspecified"
    if ftype == "text":
        return f"Sample {name.replace('_', ' ')} for {ent_name.lower()} {index}."
    if ftype == "int":
        special = {"quantity": 2, "rating": 5, "day_of_week": 1, "position": index,
                   "bedrooms": 3, "bathrooms": 2, "capacity": 50, "guests": 2,
                   "max_guests": 4, "stock": 25, "duration_minutes": 45}
        return special.get(name, index)
    if ftype == "float":
        special = {"price": 19.99, "unit_price": 19.99, "amount": 49.99, "total": 59.97,
                   "total_price": 120.50, "price_per_night": 89.0, "balance": 250.0,
                   "monthly_limit": 500.0, "salary_min": 60000.0, "salary_max": 90000.0,
                   "consultation_fee": 75.0, "progress": 0.5}
        return special.get(name, round(9.99 * index, 2))
    if ftype == "bool":
        return True
    if ftype == "datetime":
        return f"2030-01-{min(index, 27) + 1:02d}T10:00:00"
    if ftype == "date":
        return f"2030-01-{min(index, 27) + 1:02d}"
    return f"{name} {index}"


def create_payload(ent: dict[str, Any], index: int, fk_lookup: dict[str, int]) -> dict[str, Any]:
    """Request body used to create one row of this entity via the API."""
    body: dict[str, Any] = {}
    for field in ent["fields"]:
        if field.get("primary_key") or field["name"] in ("created_at", "password_hash"):
            continue
        if field["name"] in OWNER_FIELD_NAMES and field.get("ref") == "User":
            continue  # auto-assigned from the JWT
        value = sample_value(field, ent["name"], index, fk_lookup)
        if value is None and field.get("nullable"):
            continue
        body[field["name"]] = value
    return body


def py_type(field: dict[str, Any]) -> str:
    return {"str": "str", "text": "str", "int": "int", "float": "float",
            "bool": "bool", "datetime": "datetime", "date": "date",
            "fk": "int"}.get(field["type"], "str")


def ts_type(field: dict[str, Any]) -> str:
    return {"str": "string", "text": "string", "int": "number", "float": "number",
            "bool": "boolean", "datetime": "string", "date": "string",
            "fk": "number"}.get(field["type"], "string")
