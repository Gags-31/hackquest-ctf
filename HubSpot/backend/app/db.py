"""In-memory CRM store (swap for PostgreSQL/MongoDB in production)."""
from app.models import Conversation, Customer, Proposal

customers: dict[str, Customer] = {}
conversations: dict[str, Conversation] = {}
proposals: dict[str, Proposal] = {}
customer_memory: dict[str, dict] = {}
