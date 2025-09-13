import json
import pytest
from unittest.mock import patch, MagicMock

from src.llm import call_llm
from src.models import TicketResponse


def test_call_llm_returns_ticket_response():
    fake_output = {
        "answer": "Your domain is suspended due to missing WHOIS info.",
        "references": ["Policy: Domain Suspension Guidelines"],
        "action_required": "update_whois",
    }

    # Patch the get_client function inside src.llm
    with patch("src.llm.get_client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Fake chat.completions.create response
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(fake_output)))]
        )

        # Call our LLM wrapper
        res: TicketResponse = call_llm("Why is my domain suspended?")

        # Assertions
        assert isinstance(res, TicketResponse)
        assert res.answer == fake_output["answer"]
        assert res.references == fake_output["references"]
        assert res.action_required == fake_output["action_required"]
