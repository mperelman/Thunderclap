"""Diagnose the actual API error"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

print("Loading key from .env...")
load_dotenv()
key = os.getenv('GEMINI_API_KEY')
print(f"Key loaded: {key[:20]}...\n")

print("Configuring Gemini...")
genai.configure(api_key=key)

print("Creating model: gemini-2.0-flash-exp")
model = genai.GenerativeModel('gemini-2.0-flash-exp')

print("Making API call...\n")

try:
    response = model.generate_content("hi")
    print(f"[SUCCESS] {response.text}")
    
except Exception as e:
    print(f"[ERROR] {type(e).__name__}")
    print(f"\nFull error:\n{e}")
    
    error_str = str(e)
    
    # Check specific error types
    if "429" in error_str:
        print("\n[DIAGNOSIS] 429 error")
        if "limit: 0" in error_str:
            print("  - Shows 'limit: 0' (quota exhausted)")
        if "retry" in error_str.lower():
            import re
            retry_match = re.search(r'retry.*?(\d+)', error_str.lower())
            if retry_match:
                print(f"  - Asks to retry in {retry_match.group(1)}s")
    
    if "400" in error_str:
        print("\n[DIAGNOSIS] 400 error (bad request)")
    
    if "API_KEY_INVALID" in error_str:
        print("\n[DIAGNOSIS] Invalid API key")
    
    print("\n[QUESTION] Does the error message match what you see in dashboard?")


