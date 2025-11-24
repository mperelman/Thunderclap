"""Test Gemini API connection."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.llm import LLMAnswerGenerator

api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyAXr9YBivlfndzZ4azcm7g3yfgan4Xl_ls')
print(f"Testing API key: {api_key[:20]}...")

llm = LLMAnswerGenerator(api_key=api_key)
print(f"Model: {llm.client._model_name}")

# Simple test
try:
    response = llm.call_api("Say 'hello' in one word.")
    print(f"SUCCESS: {response}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

