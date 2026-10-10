"""Lightweight NLP pipeline: NER-ish, intent, sentiment, entity extraction, summary."""
import re
from collections import Counter

POSITIVE = {"good", "great", "happy", "satisfied", "excellent", "love", "thanks", "perfect"}
NEGATIVE = {"bad", "angry", "poor", "complaint", "delay", "late", "broken", "refund", "worst"}


def sentiment(text: str) -> str:
    words = set(re.findall(r"\w+", text.lower()))
    p, n = len(words & POSITIVE), len(words & NEGATIVE)
    if p > n:
        return "Positive"
    if n > p:
        return "Negative"
    return "Neutral"


def intent(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["buy", "purchase", "need", "order", "units"]):
        return "Purchase"
    if any(k in t for k in ["complaint", "issue", "problem", "delay"]):
        return "Complaint"
    if any(k in t for k in ["price", "quote", "cost", "budget"]):
        return "Pricing Inquiry"
    if "follow" in t:
        return "Follow-up"
    return "General"


def extract_entities(text: str) -> dict:
    qty = re.search(r"(\d+)\s*(units?|pieces?|pcs|items?)", text, re.I)
    budget = re.search(r"(?:₹|rs\.?|inr)\s*([\d,]+)\s*(lakh|k|thousand)?", text, re.I)
    date = re.search(r"before\s+([\w\s]+\d+\w*)", text, re.I) or re.search(r"before\s+([^.,]+)", text, re.I)
    return {
        "quantity": f"{qty.group(1)} {qty.group(2)}" if qty else None,
        "budget": (f"Rs {budget.group(1)}{' ' + budget.group(2) if budget and budget.group(2) else ''}") if budget else None,
        "delivery": f"Before {date.group(1)}" if date else None,
        "intent": intent(text),
        "priority": "High" if any(k in text.lower() for k in ["urgent", "asap", "immediately"]) else "Normal",
    }


def summarize(messages: list[str], max_sentences: int = 2) -> str:
    text = " ".join(messages)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) <= max_sentences:
        return text.strip()
    # naive extractive: sentences with most keyword hits
    counts = Counter(re.findall(r"\w+", text.lower()))
    scored = sorted(sentences, key=lambda s: sum(counts[w] for w in re.findall(r"\w+", s.lower())), reverse=True)
    return " ".join(scored[:max_sentences]).strip()
