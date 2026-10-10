from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.config import settings
from app.routers import customers, conversations, proposals, assistant, analytics
from app.agents.agents import CRMManagerAgent

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0", docs_url="/docs")
manager = CRMManagerAgent()

app.include_router(customers.router)
app.include_router(conversations.router)
app.include_router(proposals.router)
app.include_router(assistant.router)
app.include_router(analytics.router)


@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html><html><head><meta charset="utf-8"><title>HubSpot</title>
<style>body{font-family:system-ui;background:#0f172a;color:#e2e8f0;max-width:860px;margin:40px auto;padding:0 16px}
button{margin:4px;padding:10px 16px;border:0;border-radius:8px;background:#2563eb;color:#fff;cursor:pointer}
#out{white-space:pre-wrap;background:#1e293b;padding:16px;border-radius:8px;min-height:60px}
a{color:#60a5fa}</style></head><body>
<h1>HubSpot</h1><p><i>Talk to the customer. Let AI handle the CRM.</i></p>
<p><a href="/docs">API Docs</a> · Propose via <code>POST /proposals/generate</code> · Customer 360 via <code>GET /analytics/customer/&lt;id&gt;</code></p>
<h3>Agents</h3>
<button onclick="run('conversation')">Conversation</button>
<button onclick="run('nlp')">NLP Intelligence</button>
<button onclick="run('proposal')">Proposal</button>
<button onclick="run('recommendation')">Recommendation</button>
<button onclick="run('followup')">Follow-Up</button>
<button onclick="run('intelligence')">Customer Intelligence</button>
<button onclick="run('next_action')">Next Best Action</button>
<h3>Output</h3><div id="out">Ready.</div>
<script>
async function run(agent){const r=await fetch('/agents/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent,customer_id:'Consumer_001',messages:['I need 50 units and my budget is around ₹2 lakh. I need delivery before the 20th.'],name:'Rahul',conversations:14,avg_purchase:75000,sentiment:'Positive',intent:'Purchase',days:6,proposal_pending:true})});document.getElementById('out').textContent=JSON.stringify(await r.json(),null,2)}
</script></body></html>"""


@app.get("/health")
def health():
    return {"healthy": True, "project": settings.PROJECT_NAME}


@app.post("/agents/run")
def run_agent(payload: dict):
    return manager.run(payload)
