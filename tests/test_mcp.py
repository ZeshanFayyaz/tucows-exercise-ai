import re
from mcp import build_prompt

def test_prompt_includes_query_and_context():
    query = "My domain was suspended"
    retrieved = [
        {"text": "WHOIS suspension details...", "reference": "Policy: WHOIS"},
        {"text": "Account access rules...", "reference": "Policy: Account Access"},
    ]

    prompt = build_prompt(query, retrieved)

    # Must include query
    assert query in prompt

    # Must include references
    for r in retrieved:
        assert r["text"] in prompt
        assert r["reference"] in prompt

    # Must include schema keys
    for key in ["answer", "references", "action_required"]:
        assert re.search(key, prompt)
