import pytest
from fastapi.testclient import TestClient
from src.app import app
from src.models import TicketResponse

client = TestClient(app)

def test_resolve_ticket_endpoint():
    payload = {"ticket_text": "My domain was suspended"}
    response = client.post("/resolve-ticket", json=payload)
    assert response.status_code == 200

    data = response.json()
    # Validate against schema
    ticket = TicketResponse(**data)
    assert isinstance(ticket, TicketResponse)
    assert "answer" in data
    assert "references" in data
    assert "action_required" in data
