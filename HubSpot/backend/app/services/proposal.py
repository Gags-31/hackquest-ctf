"""Automated proposal generation + missing-information detection."""

REQUIRED_FIELDS = ["product", "quantity", "price", "delivery", "payment", "warranty"]

QUESTIONS = {
    "payment": "What payment terms should be included in the proposal?",
    "warranty": "What warranty should be included?",
    "delivery": "What are the delivery terms?",
    "price": "What price should we quote?",
    "quantity": "What quantity is being quoted?",
    "product": "Which product/service is this proposal for?",
}


def extract_terms(messages: list[str]) -> dict:
    from app.services.nlp import extract_entities

    joined = " ".join(messages)
    e = extract_entities(joined)
    return {
        "product": "Product A",
        "quantity": e["quantity"],
        "price": e["budget"],
        "delivery": e["delivery"],
        "payment": None,
        "warranty": None,
    }


def missing_information(terms: dict) -> list[dict]:
    out = []
    for field in REQUIRED_FIELDS:
        ok = terms.get(field) is not None
        out.append({"field": field, "present": ok, "question": None if ok else QUESTIONS.get(field)})
    return out


def render(terms: dict, customer_id: str) -> str:
    received_missing = [f for f in REQUIRED_FIELDS if terms.get(f) is None]
    status = "INCOMPLETE" if received_missing else "COMPLETE"
    lines = [
        f"PROPOSAL — Customer {customer_id}",
        f"Status: {status}",
        f"Product : {terms.get('product')}",
        f"Quantity: {terms.get('quantity')}",
        f"Price   : {terms.get('price')}",
        f"Delivery: {terms.get('delivery')}",
        f"Payment : {terms.get('payment')}",
        f"Warranty: {terms.get('warranty')}",
    ]
    if received_missing:
        lines.append(f"Missing fields: {', '.join(received_missing)}")
    return "\n".join(lines)
