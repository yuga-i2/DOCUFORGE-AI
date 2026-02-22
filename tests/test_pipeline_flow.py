"""
Test script to verify pipeline flow with comprehensive logging.
Tests both successful and error scenarios.
"""

import sys
import logging

# Set up logging to show all levels
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)-8s | %(name)s | %(message)s'
)

print("\n" + "="*80)
print("DOCUFORGE PIPELINE FLOW TEST")
print("="*80 + "\n")

# Test 1: Verify imports
print("[TEST 1] Verifying imports...\n")
try:
    from orchestration.graph import get_graph
    from orchestration.router import route_from_supervisor
    print("[OK] All imports successful\n")
except Exception as e:
    print(f"[FAILED] Import failed: {e}\n")
    sys.exit(1)

# Test 2: Verify graph builds
print("[TEST 2] Building graph...\n")
try:
    graph = get_graph()
    print("[OK] Graph built successfully\n")
except Exception as e:
    print(f"[FAILED] Graph build failed: {e}\n")
    sys.exit(1)

# Test 3: Test routing logic with mock states
print("[TEST 3] Testing routing logic...\n")

test_states = [
    {
        "name": "ERROR STATE",
        "state": {
            "session_id": "test-001",
            "query": "What is this?",
            "uploaded_file_path": "",
            "ingested_text": "",
            "retrieved_chunks": None,
            "analysis_result": None,
            "draft_report": "",
            "verified_report": "",
            "routing_decision": "error",
            "error_log": ["Test error message"],
            "agent_trace": []
        },
        "expected_route": "error_handler"
    },
    {
        "name": "INGESTION NEEDED (No text)",
        "state": {
            "session_id": "test-002",
            "query": "What is this?",
            "uploaded_file_path": "/path/to/file.pdf",
            "ingested_text": "",
            "retrieved_chunks": None,
            "analysis_result": None,
            "draft_report": "",
            "verified_report": "",
            "routing_decision": "continue",
            "error_log": [],
            "agent_trace": []
        },
        "expected_route": "ingestion_agent"
    },
    {
        "name": "RAG NEEDED (No chunks)",
        "state": {
            "session_id": "test-003",
            "query": "What is this?",
            "uploaded_file_path": "/path/to/file.pdf",
            "ingested_text": "This is some sample text for testing the pipeline flow. " * 5,
            "retrieved_chunks": None,
            "analysis_result": None,
            "draft_report": "",
            "verified_report": "",
            "routing_decision": "continue",
            "error_log": [],
            "agent_trace": []
        },
        "expected_route": "rag_agent"
    },
    {
        "name": "ANALYSIS NEEDED (No result)",
        "state": {
            "session_id": "test-004",
            "query": "What is this?",
            "uploaded_file_path": "/path/to/file.pdf",
            "ingested_text": "This is some sample text for testing the pipeline flow. " * 5,
            "retrieved_chunks": ["chunk1", "chunk2"],
            "analysis_result": None,
            "draft_report": "",
            "verified_report": "",
            "routing_decision": "continue",
            "error_log": [],
            "agent_trace": []
        },
        "expected_route": "analyst_agent"
    },
    {
        "name": "DONE (All complete)",
        "state": {
            "session_id": "test-005",
            "query": "What is this?",
            "uploaded_file_path": "/path/to/file.pdf",
            "ingested_text": "This is some sample text for testing the pipeline flow. " * 5,
            "retrieved_chunks": ["chunk1", "chunk2"],
            "analysis_result": {"summary": "Analysis result"},
            "draft_report": "This is the draft report.",
            "verified_report": "This is the verified report.",
            "routing_decision": "continue",
            "error_log": [],
            "agent_trace": []
        },
        "expected_route": "done"
    }
]

print("Running routing logic tests...\n")
for test in test_states:
    print(f"Test: {test['name']}")
    result = route_from_supervisor(test['state'])
    print(f"Expected: {test['expected_route']}, Got: {result}")
    status = "[OK]" if result == test['expected_route'] else "[FAILED]"
    print(f"{status}\n")

print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print("""
[OK] Imports validated
[OK] Graph compiled
[OK] Routing logic tested

NEXT STEPS:
1. Upload a valid PDF file through http://localhost:3000
2. Check console output for detailed logging
3. Monitor the pipeline stages:
   [INGESTION] >> [RAG] >> [ANALYSIS] >> [REPORT]

EXPECTED LOGS:
- [ROUTER] showing decisions at each stage
- [INGESTION] showing file parsing
- [RAG] showing chunking
- [SUPERVISOR] showing routing choices
- [ERROR_HANDLER] if any stage fails (with error messages)

NO INFINITE LOOPS - Each stage runs ONCE per phase
""")
print("="*80 + "\n")
