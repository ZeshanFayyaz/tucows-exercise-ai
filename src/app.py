"""
This module defines the FastAPI application for the knowledge assistant. 
It exposes two endpoints:

- POST / resolve-ticket:
    Takes a customer support ticket, retrieves the most relevant documentation
    using the knowledge base, builds an MCP-compliant prompt, and calls the 
    LLM to generate a structured JSON response

- GET /ping:
    - Simple health check to make sure the API is running 

This file serves as the entry point for the service
"""

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
    """
    Main API endpoint: resolve a customer support ticket. 

    Performed by the following steps: 
    1. Load the knowledge base (only once)
    2. Retrieve the top-k most relevant document chunks 
    3. Build an MCP compliant prompt
    4. Send the prompt to the LLM and return a validated response
    """
    global kb
    if kb is None:
        kb = KnowledgeBase()

    retrieved = kb.retrieve(ticket.ticket_text, top_k=3)
    prompt = build_prompt(ticket.ticket_text, retrieved)
    response = call_llm(prompt)
    return response

@app.get("/ping")
def ping():
    """
    Simple health check endpoint
    Useful for testing whether the API is up and running
    """
    return {"status": "ok"}
