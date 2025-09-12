from pydantic import BaseModel, Field
from typing import List

class TicketRequest(BaseModel):
    ticket_text: str = Field(..., description="Raw customer support ticket text")

class TicketResponse(BaseModel):
    answer: str
    references: List[str]
    action_required: str
