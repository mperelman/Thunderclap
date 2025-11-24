"""Make ONE clean API call with NO automatic retries"""
import sys
sys.path.insert(0, '.')

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
key = os.getenv('GEMINI_API_KEY')

print(f"Using key: {key[:20]}...")
print("Configuring with NO automatic retries...")

genai.configure(api_key=key)

# Create model with custom settings to disable retries
model = genai.GenerativeModel(
    'gemini-2.0-flash-exp',
    # Configure to not retry on failure
)

print("Making ONE clean API call...")
print()

try:
    # Single call - if it fails, it fails (no retries)
    response = model.generate_content(
        "Say: test",
        request_options={'retry': None}  # Disable retries
    )
    
    print(f"[SUCCESS] {response.text}")
    print("\nAPI key is working! Now we can proceed.")
    
except Exception as e:
    error_str = str(e)
    
    if "429" in error_str:
        # Extract retry time
        import re
        retry_match = re.search(r'retry.*?(\d+)s', error_str, re.IGNORECASE)
        if retry_match:
            wait_time = int(retry_match.group(1))
            print(f"[RATE LIMIT] Need to wait {wait_time} more seconds")
        else:
            print("[RATE LIMIT] Per-minute limit hit")
    else:
        print(f"[ERROR] {error_str[:200]}")


