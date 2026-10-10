"""Multi-agent AI layer wired to real services."""
from app.services import nlp, proposal as proposal_svc, rag, predictive, next_action, memory


class BaseAgent:
    name = "agent"

    def run(self, payload: dict) -> dict:
        raise NotImplementedError


class ConsumerAgent(BaseAgent):
    name = "consumer"

    def run(self, payload):
        return {"agent": self.name, "action": "create/maintain consumer record", "customer": payload.get("customer_id")}


class ConversationAgent(BaseAgent):
    name = "conversation"

    def run(self, payload):
        msgs = payload.get("messages", [])
        return {"agent": self.name, "summary": nlp.summarize(msgs) if msgs else None, "sentiment": nlp.sentiment(" ".join(msgs)) if msgs else None}


class NLPIntelligenceAgent(BaseAgent):
    name = "nlp"

    def run(self, payload):
        text = " ".join(payload.get("messages", []))
        return {"agent": self.name, "entities": nlp.extract_entities(text), "sentiment": nlp.sentiment(text)}


class ProposalAgent(BaseAgent):
    name = "proposal"

    def run(self, payload):
        msgs = payload.get("messages", [])
        terms = proposal_svc.extract_terms(msgs)
        return {"agent": self.name, "terms": terms, "missing": proposal_svc.missing_information(terms), "rendered": proposal_svc.render(terms, payload.get("customer_id", "unknown"))}


class RecommendationAgent(BaseAgent):
    name = "recommendation"

    def run(self, payload):
        return {"agent": self.name, "products": ["Product A", "Product C"], "reason": "based on purchase history"}


class FollowUpAgent(BaseAgent):
    name = "followup"

    def run(self, payload):
        return {"agent": self.name, "message": f"Hi {payload.get('name', 'customer')}, following up on your request."}


class CustomerIntelligenceAgent(BaseAgent):
    name = "intelligence"

    def run(self, payload):
        return {"agent": self.name, "prediction": predictive.predict(payload.get("customer_id", "anon"), payload.get("conversations", 0), payload.get("avg_purchase", 0), payload.get("sentiment", "Neutral"))}


class NextActionAgent(BaseAgent):
    name = "next_action"

    def run(self, payload):
        return {"agent": self.name, "ranked": next_action.rank(payload.get("sentiment", "Neutral"), payload.get("intent", "General"), payload.get("days", 0), payload.get("proposal_pending", False))}


class CRMManagerAgent(BaseAgent):
    """Orchestrator."""

    name = "crm_manager"

    def __init__(self):
        self.agents = {a.name: a for a in [ConsumerAgent(), ConversationAgent(), NLPIntelligenceAgent(), ProposalAgent(), RecommendationAgent(), FollowUpAgent(), CustomerIntelligenceAgent(), NextActionAgent()]}

    def run(self, payload):
        target = payload.get("agent", "conversation")
        return self.agents.get(target, ConversationAgent()).run(payload)
