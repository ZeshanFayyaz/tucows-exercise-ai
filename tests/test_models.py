import pytest
from models import TicketRequest, TicketResponse

def test_ticket_request_validates():
    req = TicketRequest(ticket_text="My domain is suspended")
    assert req.ticket_text == "My domain is suspended"

def test_ticket_response_schema_roundtrip():
    res = TicketResponse(
        answer="Test answer",
        references=["doc1", "doc2"],
        action_required="reset_password",
    )
    assert res.answer == "Test answer"
    assert res.references == ["doc1", "doc2"]
    assert res.action_required == "reset_password"


