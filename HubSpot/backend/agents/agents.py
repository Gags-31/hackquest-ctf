class Agent:
    name = "agent"

    def run(self, payload: dict) -> dict:
        raise NotImplementedError


class ConsumerAgent(Agent):
    name = "consumer"

    def run(self, payload):
        return {"agent": self.name, "action": "create/maintain consumer record"}


class ConversationAgent(Agent):
    name = "conversation"

    def run(self, payload):
        return {"agent": self.name, "action": "record conversation & summarize"}


class NLPIntelligenceAgent(Agent):
    name = "nlp"

    def run(self, payload):
        return {"agent": self.name, "action": "extract requirements, intent, sentiment"}


class ProposalAgent(Agent):
    name = "proposal"

    def run(self, payload):
        return {"agent": self.name, "action": "generate proposal from agreed terms"}


class RecommendationAgent(Agent):
    name = "recommendation"

    def run(self, payload):
        return {"agent": self.name, "action": "recommend products / next action"}


class FollowUpAgent(Agent):
    name = "followup"

    def run(self, payload):
        return {"agent": self.name, "action": "prepare follow-ups"}


class CustomerIntelligenceAgent(Agent):
    name = "intelligence"

    def run(self, payload):
        return {"agent": self.name, "action": "analyze behavior / churn / CLV"}


class CRMManagerAgent(Agent):
    """Orchestrator: decides which agent handles which task."""

    name = "crm_manager"

    def __init__(self):
        self.agents = {
            "consumer": ConsumerAgent(),
            "conversation": ConversationAgent(),
            "nlp": NLPIntelligenceAgent(),
            "proposal": ProposalAgent(),
            "recommendation": RecommendationAgent(),
            "followup": FollowUpAgent(),
            "intelligence": CustomerIntelligenceAgent(),
        }

    def run(self, payload):
        target = payload.get("agent", "conversation")
        agent = self.agents.get(target, self.agents["conversation"])
        return agent.run(payload)
