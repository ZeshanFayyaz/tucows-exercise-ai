from fastapi import FastAPI
from .models import TicketRequest, TicketResponse
from .rag import KnowledgeBase
from .mcp import build_prompt
from .llm import call_llm

app = FastAPI(title="Knowledge Assistant", version="1.0.0")

# Build knowledge base on startup
kb = KnowledgeBase()

@app.post("/resolve-ticket", response_model=TicketResponse)
def resolve_ticket(ticket: TicketRequest) -> TicketResponse:
    """
    Main entrypoint: takes a support ticket, retrieves context,
    builds MCP prompt, calls the LLM, and returns structured JSON.
    """
    # Step 1: Retrieve relevant chunks
    retrieved = kb.retrieve(ticket.ticket_text, top_k=3)

    # Step 2: Build MCP prompt
    prompt = build_prompt(ticket.ticket_text, retrieved)

    # Step 3: Call LLM and return TicketResponse
    response = call_llm(prompt)
    return response
