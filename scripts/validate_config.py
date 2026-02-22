import yaml

with open('config/docuforge_config.yaml') as f:
    config = yaml.safe_load(f)

print('[OK] Config YAML valid')
print("Verifier settings:")
print(f"  - min_faithfulness_score: {config['verifier']['min_faithfulness_score']}")
print(f"  - max_reflection_loops: {config['verifier']['max_reflection_loops']}")
print(f"  - hallucination_threshold: {config['verifier']['hallucination_threshold']}")
print(f"  - min_claims_to_verify: {config['verifier']['min_claims_to_verify']}")
print("\nWriter settings:")
print(f"  - max_context_chars: {config['writer']['max_context_chars']}")
print(f"  - prompt_version: {config['writer']['prompt_version']}")
print("\nAnalyst settings:")
print(f"  - force_json_output: {config['analyst']['force_json_output']}")
print(f"  - json_retry_attempts: {config['analyst']['json_retry_attempts']}")
