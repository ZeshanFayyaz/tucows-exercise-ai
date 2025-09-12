from fastapi import FastAPI
from .models import TicketRequest, TicketResponse
from .rag import KnowledgeBase
from .mcp import build_prompt
from .llm import call_llm

app = FastAPI(title="Knowledge Assistant", version="1.0.0")

# Lazy init
kb = None

@app.post("/resolve-ticket", response_model=TicketResponse)
def resolve_ticket(ticket: TicketRequest) -> TicketResponse:
    global kb
    if kb is None:
        kb = KnowledgeBase()

    retrieved = kb.retrieve(ticket.ticket_text, top_k=3)
    prompt = build_prompt(ticket.ticket_text, retrieved)
    response = call_llm(prompt)
    return response

@app.get("/ping")
def ping():
    return {"status": "ok"}
