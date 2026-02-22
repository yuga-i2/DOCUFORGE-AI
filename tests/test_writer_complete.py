#!/usr/bin/env python3
"""Test the complete writer_agent flow."""
from agents.writer_agent import (
    _get_prompt_version_from_trace,
    _load_prompt_template,
    _render_prompt,
    _check_context_coverage,
)

# Test 1: Version extraction
agent_trace = ["pipeline: using prompt version v2", "other entries"]
version = _get_prompt_version_from_trace(agent_trace)
assert version == "v2", f"Expected v2, got {version}"
print(f"[OK] Version extraction: {version}")

# Test 2: Template loading
template = _load_prompt_template(version)
assert "{query}" in template, "Template missing {query}"
assert "{document_context}" in template, "Template missing {document_context}"
print(f"[OK] Template loaded ({len(template)} chars)")

# Test 3: Template rendering
filled = _render_prompt(template, "my query", "doc content", "analysis", "web")
assert "my query" in filled, "Query not in filled prompt"
assert "doc content" in filled, "Doc not in filled prompt"
print(f"[OK] Template rendering ({len(filled)} chars)")

# Test 4: Context coverage check
good_context = "This is a document " * 20  # > 200 chars
bad_context = "Short"  # < 200 chars
assert _check_context_coverage(good_context, "query") == True, "Should accept good context"
assert _check_context_coverage(bad_context, "query") == False, "Should reject short context"
print("[OK] Context coverage validation")

print("\n[SUCCESS] All writer_agent helpers working correctly!")
