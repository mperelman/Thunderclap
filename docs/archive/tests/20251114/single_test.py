"""ONE single API test - no waste"""
import os
from dotenv import load_dotenv
load_dotenv(override=True)

import google.generativeai as genai

key = os.getenv('GEMINI_API_KEY')
print(f"Using key: {key[:20]}...")

genai.configure(api_key=key)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# ONE test call only
response = model.generate_content("Say: ok")
print(f"\n[SUCCESS] API works! Response: {response.text}")
print("\nQuota is NOT exhausted. Ready to proceed.")

