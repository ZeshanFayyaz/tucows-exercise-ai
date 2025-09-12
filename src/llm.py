import os
import json
import re
from typing import Any, Dict
from pydantic import ValidationError
from openai import OpenAI

from .models import TicketResponse

# Expanded set of allowed actions
ALLOWED_ACTIONS = {
    "none",
    "escalate_to_abuse_team",
    "escalate_to_billing",
    "escalate_to_registrar",
    "escalate_to_dns_team",
    "escalate_to_legal",
    "escalate_to_support_manager",
    "reset_password",
    "update_whois",
    "verify_identity",
    "transfer_domain",
    "request_more_info",
}

def get_client() -> OpenAI:
    """
    Create an OpenAI-compatible client.
    Works with OpenAI or Ollama (set OPENAI_BASE_URL).
    """
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY", "EMPTY")
    if base_url:
        return OpenAI(base_url=base_url, api_key=api_key)
    return OpenAI(api_key=api_key)

def _strip_to_json(text: str) -> str:
    """
    Extract the first {...} JSON block from model output.
    Removes ```json fences if present.
    """
    if "```" in text:
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.DOTALL)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text

def _coerce_to_schemaish(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize shapes before Pydantic validation.
    - references -> list[str]
    - action_required -> one of ALLOWED_ACTIONS
    - answer -> string
    """
    refs = data.get("references", [])
    if isinstance(refs, str):
        refs = [refs]
    elif not isinstance(refs, list):
        refs = []
    data["references"] = [str(r) for r in refs]

    act = str(data.get("action_required", "request_more_info"))
    if act not in ALLOWED_ACTIONS:
        act = "request_more_info"
    data["action_required"] = act

    data["answer"] = str(data.get("answer", ""))

    return data

def call_llm(prompt: str, model: str | None = None) -> TicketResponse:
    """
    Call the LLM with the MCP prompt and enforce JSON schema.
    Returns a validated TicketResponse.
    """
    client = get_client()
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    messages = [
        {
            "role": "system",
            "content": (
                "You are a careful assistant. "
                "Return ONLY valid JSON, no code fences, no prose."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    # First attempt
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0,
    )
    text = resp.choices[0].message.content.strip()

    # Parse
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        text = _strip_to_json(text)
        data = json.loads(text)

    # Validate
    try:
        data = _coerce_to_schemaish(data)
        return TicketResponse(**data)
    except (ValidationError, TypeError, json.JSONDecodeError):
        # One repair pass
        repair_messages = messages + [
            {
                "role": "system",
                "content": (
                    "Your last reply was not valid JSON. "
                    "Reply again with ONLY the JSON object matching the schema."
                ),
            }
        ]
        resp2 = client.chat.completions.create(
            model=model,
            messages=repair_messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
        text2 = resp2.choices[0].message.content.strip()
        text2 = _strip_to_json(text2)
        data2 = json.loads(text2)
        data2 = _coerce_to_schemaish(data2)
        return TicketResponse(**data2)
