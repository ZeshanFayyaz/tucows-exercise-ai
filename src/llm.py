"""
This module provides a wrapper around the LLM backend 

It is responsible for the following: 

1. Building a client for Ollama 
2. Sending MCP-compliant prompts and enforcing JSON-only responses 
3. Handling common failure cases, such as: 
    - Malformed JSON
    - Invalid schema fields 
    - API errors 
4. Guaranteeing that every call produces a valid 'TicketResponse' object
   such that the rest of the assistant never has to worry about validation 
"""

import os
import json
import re
from typing import Any, Dict, Optional

from pydantic import ValidationError
from openai import OpenAI, APIConnectionError, RateLimitError, APIStatusError

from .models import TicketResponse
from .mcp import ALLOWED_ACTIONS  # single source of truth


def get_client() -> OpenAI:
    """
    Create an OpenAI-compatible client.
    - Works with OpenAI directly (set OPENAI_API_KEY).
    - Works with OpenAI-compatible servers (set OPENAI_BASE_URL and OPENAI_API_KEY, e.g., 'sk-noop').
    """
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY", "EMPTY")

    # Configure client if using a custom base_url
    if base_url:
        return OpenAI(base_url=base_url, api_key=api_key)

    # Otherwise, return to default
    return OpenAI(api_key=api_key)


def _strip_to_json(text: str) -> str:
    """
    Extract the first {...} JSON block from model output.
    Removes ```json ..```  fences if present.
    """
    if "```" in text:
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.DOTALL)
    
    # Find the first and last braces and return the enclosed block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def _coerce_to_schemaish(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize shapes before Pydantic validation.
    - references -> list[str]
    - action_required -> one of ALLOWED_ACTIONS (fallback: request_more_info)
    - answer -> str
    """
    refs = data.get("references", []) # Normalize references
    if isinstance(refs, str):
        refs = [refs] # Wrap in list
    elif not isinstance(refs, list):
        refs = [] # Fallback
    data["references"] = [str(r) for r in refs]

    # Normalize
    act = str(data.get("action_required", "request_more_info"))
    if act not in ALLOWED_ACTIONS:
        act = "request_more_info"
    data["action_required"] = act

    # Ensure answer is a string
    data["answer"] = str(data.get("answer", ""))
    return data


def _fallback_ticket(message: str) -> TicketResponse:
    """
    Fallback TicketResponse if LLM fails or times out.
    - Returns a safe, minimal response instead of crashing the API.
    """
    return TicketResponse(
        answer=message,
        references=[],
        action_required="request_more_info",
    )


def call_llm(prompt: str, model: Optional[str] = None) -> TicketResponse:
    """
    Main entrypoint: call the LLM with a structured MCP prompt.
    - Sends messages to the model and requests JSON-only output.
    - Attempts parsing and coercion into TicketResponse schema.
    - If output is invalid JSON, performs one repair attempt.
    - If API errors occur, falls back gracefully.
    """
    client = get_client()
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    messages = [
        {
            "role": "system",
            "content": "You are a careful assistant. Return ONLY valid JSON, no code fences, no prose.",
        },
        {"role": "user", "content": prompt},
    ]

    try:
        # First attempt (ask the model to return a JSON object)
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
            timeout=30,
        )
        text = resp.choices[0].message.content.strip()

        # Try parsing a JSON direcrtly
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
                timeout=30,
            )
            text2 = resp2.choices[0].message.content.strip()
            text2 = _strip_to_json(text2)
            data2 = json.loads(text2)
            data2 = _coerce_to_schemaish(data2)
            return TicketResponse(**data2)

    # Error handling mechanism
    except (APIConnectionError, RateLimitError, APIStatusError) as e:
        return _fallback_ticket(f"LLM API error: {e.__class__.__name__}: {str(e)}")
    except Exception as e:
        # Last-resort guard so the API never 500s
        return _fallback_ticket(f"LLM unexpected error: {str(e)}")
