#!/usr/bin/env python
import google.generativeai as genai
import os

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    print("Available Gemini models for generateContent:")
    print("=" * 60)
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(f"✓ {m.name}")
    print("=" * 60)
else:
    print("ERROR: GEMINI_API_KEY not set in environment")
