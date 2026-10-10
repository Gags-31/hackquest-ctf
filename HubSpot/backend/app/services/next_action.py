ACTIONS = [
    "Call Customer",
    "Send Message",
    "Generate Proposal",
    "Recommend Product",
    "Offer Discount",
    "Schedule Follow-up",
    "Escalate Complaint",
    "Request Missing Information",
    "Do Nothing",
]


def rank(sentiment: str, last_intent: str, days_since_contact: int, proposal_pending: bool) -> list[dict]:
    scored = []
    for a in ACTIONS:
        score = 0
        if a == "Escalate Complaint" and (sentiment == "Negative" or last_intent == "Complaint"):
            score += 5
        if a == "Generate Proposal" and (last_intent == "Purchase" or (proposal_pending and sentiment != "Negative")):
            score += 4
        if a == "Send Message" and days_since_contact >= 3:
            score += 3
        if a == "Schedule Follow-up" and days_since_contact >= 7:
            score += 3
        if a == "Call Customer" and days_since_contact >= 14:
            score += 2
        if a == "Offer Discount" and sentiment == "Negative":
            score += 2
        if a == "Request Missing Information" and proposal_pending:
            score += 2
        if a == "Recommend Product":
            score += 1
        scored.append({"action": a, "score": score})
    return sorted(scored, key=lambda x: x["score"], reverse=True)
