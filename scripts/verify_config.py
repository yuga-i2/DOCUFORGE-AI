#!/usr/bin/env python3
"""Verify configuration file."""
import yaml

config = yaml.safe_load(open('config/docuforge_config.yaml'))
print("[OK] YAML valid")
print(f"RAG top_k_results: {config['rag']['top_k_results']}")
print(f"RAG chunk_size: {config['rag']['chunk_size']}")
print(f"Verifier min_faithfulness_score: {config['verifier']['min_faithfulness_score']}")
print(f"Verifier max_reflection_loops: {config['verifier']['max_reflection_loops']}")
