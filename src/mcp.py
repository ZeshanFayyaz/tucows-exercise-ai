from typing import List, Dict

def build_prompt(query: str, retrieved_chunks: List[Dict]) -> str:
    """
    Build an MCP-compliant prompt to send to the LLM.
    """
    role = "You are a Knowledge Assistant helping the support team resolve customer tickets."
    
    context_lines = []
    for c in retrieved_chunks:
        context_lines.append(f"[{c['reference']}] {c['text']}")
    context = "\n".join(context_lines)

    task = (
        "Using ONLY the provided context, answer the user's query. "
        "If information is missing, respond with what is available and set action_required accordingly. "
        "Always reply in strict JSON with the following schema:"
    )

    schema = """{
  "answer": "string",
  "references": ["list of strings"],
  "action_required": "one of: none | escalate_to_abuse_team | escalate_to_billing | escalate_to_registrar | request_more_info"
}"""

    return f"{role}\n\n<context>\n{context}\n</context>\n\n<task>\n{task}\n{schema}\n</task>\n\n<query>\n{query}\n</query>"
