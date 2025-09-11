from pydantic import BaseModel, Field
from typing import List

class TicketRequest(BaseModel):
    """
    Schema for incoming support tickets.
    The client sends a piece of free-text describing their issue.
    """
    ticket_text: str = Field(..., description="Raw customer support ticket text")


class TicketResponse(BaseModel):
    """
    Schema for outgoing answers.
    Must always conform to the MCP (Model Context Protocol) format.
    """
    answer: str
    references: List[str]
    action_required: str
