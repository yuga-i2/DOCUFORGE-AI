#!/usr/bin/env python3
"""Test the _load_prompt_template function."""
import sys
sys.path.insert(0, '.')
from agents.writer_agent import _load_prompt_template

# Test loading v3
template_v3 = _load_prompt_template("v3")
if "{query}" in template_v3 and "{document_context}" in template_v3:
    print("[OK] V3 prompt loaded with correct variables")
else:
    print("[ERROR] V3 prompt missing variables")

# Test loading non-existent version (should fallback)
template_fallback = _load_prompt_template("v99")
if "{query}" in template_fallback and "valid JSON only" in template_fallback:
    print("[OK] Fallback prompt loaded correctly")
else:
    print("[ERROR] Fallback prompt incomplete")

print(f"[OK] Prompt templates working - {len(template_v3)} chars for v3, {len(template_fallback)} chars for fallback")
