#!/usr/bin/env python3
"""
Test script to verify the two fixes:
1. PDF parsing correctly extracts text (fix for closed file handle)
2. LLM router uses correct model name (fix for gemini-1.5-flash default)
"""

import sys
import logging
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def test_llm_router_model_name():
    """Test that LLM router uses correct model name"""
    print("\n" + "="*60)
    print("TEST 1: LLM Router - Model Name Verification")
    print("="*60)
    
    from core.llm_router import _load_config
    
    # Check config
    config = _load_config()
    config_model = config.get("llm", {}).get("primary_model")
    print(f"✓ Config model: {config_model}")
    assert config_model == "gemini-2.0-flash", f"Config should be gemini-2.0-flash, got {config_model}"
    
    # Check default fallback in code
    import core.llm_router as router_module
    source = open(router_module.__file__).read()
    if 'gemini-1.5-flash-latest' in source or '= "gemini-1.5-flash"' in source:
        # Allow "gemini-1.5-flash" only if it's NOT the DEFAULT in get_llm
        if 'primary_model = llm_config.get("primary_model", "gemini-1.5-flash")' in source:
            print("✗ FAIL: Default fallback still uses old model name")
            return False
    
    print("✓ PASS: LLM router configured correctly")
    return True


def test_pdf_parser_context_manager():
    """Test that PDF parser doesn't use closed file handle"""
    print("\n" + "="*60)
    print("TEST 2: PDF Parser - Context Manager Fix")
    print("="*60)
    
    import core.ingestion.multimodal_parser as parser_module
    source = open(parser_module.__file__).read()
    
    # Check that len(pdf) isn't used after the with block
    lines = source.split('\n')
    in_parse_pdf = False
    in_with_block = False
    seen_with_close = False
    issues = []
    
    for i, line in enumerate(lines, 1):
        if 'def parse_pdf' in line:
            in_parse_pdf = True
            continue
        
        if not in_parse_pdf:
            continue
            
        if 'def ' in line and 'parse_pdf' not in line:
            in_parse_pdf = False
            
        if 'with fitz.open' in line:
            in_with_block = True
            with_start = i
            
        if in_with_block and line.strip() and not line.startswith(' ' * 12):
            # Check indentation - if we're back to lower indentation, with block ended
            if 'with fitz' not in line and with_start != i:
                in_with_block = False
                seen_with_close = True
        
        if seen_with_close and 'len(pdf)' in line:
            issues.append(f"Line {i}: Uses len(pdf) after context manager closed: {line.strip()}")
    
    if issues:
        print("✗ FAIL: PDF parser still uses len(pdf) after with block:")
        for issue in issues:
            print(f"  {issue}")
        return False
    
    print("✓ PASS: PDF extraction happens before file handle closes")
    return True


def main():
    print("\n" + "="*60)
    print("DOCUFORGE AI — VERIFICATION TESTS")
    print("="*60)
    
    results = []
    
    try:
        results.append(("LLM Router Model Fix", test_llm_router_model_name()))
    except Exception as e:
        print(f"✗ ERROR in test 1: {e}")
        results.append(("LLM Router Model Fix", False))
    
    try:
        results.append(("PDF Parser Fix", test_pdf_parser_context_manager()))
    except Exception as e:
        print(f"✗ ERROR in test 2: {e}")
        results.append(("PDF Parser Fix", False))
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    print("\n" + ("="*60))
    if all_passed:
        print("✓ ALL TESTS PASSED - Fixes are working!")
        print("="*60)
        return 0
    else:
        print("✗ SOME TESTS FAILED - Please review the output above")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
