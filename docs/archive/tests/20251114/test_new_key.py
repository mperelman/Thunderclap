"""Quick test of new API key"""
import sys
sys.path.insert(0, '.')

from google import genai
from lib.api_key_manager import APIKeyManager

print("Testing new API key...\n")

km = APIKeyManager()
key = km.get_current_key()

print(f"Using key: {key[:20]}...\n")

try:
    client = genai.Client(api_key=key)
    
    # Simple test
    response = client.models.generate_content(
        model='models/gemini-2.5-flash',
        contents='Say "hi" in one word'
    )
    
    print("[SUCCESS] New key works!")
    print(f"Response: {response.text}")
    print("\nReady to submit batch job!")
    print("Run: python scripts/run_batch_detection.py")

except Exception as e:
    error_msg = str(e)
    
    if '429' in error_msg or 'quota' in error_msg.lower():
        print("[QUOTA EXHAUSTED] This key is also exhausted")
        print("Try another key or wait for reset")
    else:
        print(f"[ERROR] {error_msg[:200]}")

