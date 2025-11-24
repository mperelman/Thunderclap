"""Show raw error without parsing"""
import sys
sys.path.insert(0, '.')

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
key = os.getenv('GEMINI_API_KEY')

print("Making ONE API call, will show RAW error...\n")

genai.configure(api_key=key)
model = genai.GenerativeModel('gemini-2.0-flash')  # Stable (not experimental)

try:
    response = model.generate_content("test")
    print(f"[SUCCESS] {response.text}")
    
except Exception as e:
    print("[FULL ERROR]:")
    print(str(e))

