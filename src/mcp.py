"""
This module defines the MCP prompt-building layer. It adheres strictly to MSP policies. 

It is responsible for the following: 

1. Defining the allowed set of 'action_required' values that the LLM can return 
    - Centralized as a single source of truth for validation and testing

2. Constructing structured prompts for the LLM 
    - Wraps the user's ticket text and knowledge base chinks
    - Injects context into a strict schema definition 
    - Enforces MCP princples
        - Context grounding 
        - Explicit task definition 
        - Schema compliance

3. Returning a formatted string prompt that tells the model: 
    - Who it is 
    - What context to use 
    - What format to respond in
"""

from typing import List, Dict

ALLOWED_ACTIONS = [
    "none", "escalate_to_abuse_team", "escalate_to_billing", "escalate_to_registrar",
    "escalate_to_dns_team", "escalate_to_legal", "escalate_to_support_manager",
    "reset_password", "update_whois", "verify_identity", "transfer_domain", "request_more_info",
]

def build_prompt(query: str, retrieved_chunks: List[Dict]) -> str:
    role = "You are a Knowledge Assistant helping the support team resolve customer tickets."
    context_lines = [f"Source: {c['reference']}\n\"{c['text']}\"" for c in retrieved_chunks]
    context = "\n\n".join(context_lines)

    task = (
        "Using ONLY the provided context, answer the user's query. "
        "If information is missing, respond with what is available and set action_required accordingly. "
        "Always reply in strict JSON with the following schema:"
    )
    schema = f"""{{
  "answer": "string",
  "references": ["list of strings"],
  "action_required": "one of: {' | '.join(ALLOWED_ACTIONS)}"
}}"""

    return (
        f"{role}\n\n"
        f"<context>\n{context}\n</context>\n\n"
        f"<task>\n{task}\n{schema}\n</task>\n\n"
        f"<query>\n{query}\n</query>"
    )
