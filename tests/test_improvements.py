#!/usr/bin/env python3
"""Test new RAG and verifier improvements."""
from agents.writer_agent import _render_prompt, _check_context_coverage
from agents.analyst_agent import _safe_parse_json

print("[TEST] _render_prompt function")
template = "Query: {query}\nContext: {document_context}\nAnalysis: {analysis_summary}\nWeb: {web_context}"
rendered = _render_prompt(template, "test query", "test content", "test analysis", "test web")
assert "{query}" not in rendered
assert "test query" in rendered
print("  ✓ Template variables replaced correctly")

print("\n[TEST] _check_context_coverage function")
assert _check_context_coverage("x" * 200, "test") == True
assert _check_context_coverage("x" * 100, "test") == False
print("  ✓ Context coverage check working")

print("\n[TEST] _safe_parse_json function")
# Test JSON with markdown fences
json_with_fences = "```json\n{\"key\": \"value\"}\n```"
parsed = _safe_parse_json(json_with_fences)
assert parsed["key"] == "value"
print("  ✓ Markdown fence removal working")

# Test JSON with extra text
json_with_text = "Here's the JSON:\n{\"score\": 0.85}\nMore text"
parsed = _safe_parse_json(json_with_text)
assert parsed["score"] == 0.85
print("  ✓ JSON extraction working")

print("\n[OK] All tests passed - RAG and verification improvements ready")
