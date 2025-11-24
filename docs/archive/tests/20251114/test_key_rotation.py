"""Test if API key rotation actually works"""
import sys
import os
sys.path.insert(0, '.')

from lib.api_key_manager import APIKeyManager
import google.generativeai as genai

print("Testing API key rotation...\n")

# Load keys
km = APIKeyManager()
print(f"Loaded {len(km.keys)} keys\n")

# Test each key individually
for i in range(len(km.keys)):
    key = km.keys[i]
    print(f"Testing Key #{i+1}: {key[:20]}...")
    
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Make a tiny test call
        response = model.generate_content("Say 'hi'")
        print(f"  [WORKS] Response: {response.text[:20]}")
        
    except Exception as e:
        error_msg = str(e)
        if '429' in error_msg or 'quota' in error_msg.lower():
            print(f"  [QUOTA EXHAUSTED]")
        else:
            print(f"  [ERROR] {error_msg[:100]}")
    
    print()

print("\nConclusion:")
print("  - If ALL keys show 'QUOTA EXHAUSTED', they share one project")
print("  - If SOME work, rotation should work")
print("  - If ALL show other errors, keys are invalid")

