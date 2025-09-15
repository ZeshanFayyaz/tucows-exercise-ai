"""
Defines the core Pydantic schemas used by the API.

- TicketRequest: input model for incoming support tickets (raw free-text).
- TicketResponse: output model enforcing MCP JSON format with
  'answer', 'references', and 'action_required'.

The purpose is to provide a strict contract between the FastAPI server,
the LLM pipeline, and external clients.
"""

from pydantic import BaseModel, Field
from typing import List

class TicketRequest(BaseModel):
    ticket_text: str = Field(..., description="Raw customer support ticket text")

class TicketResponse(BaseModel):
    answer: str
    references: List[str]
    action_required: str
