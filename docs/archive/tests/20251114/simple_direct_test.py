"""Simple direct test - no server, just the query engine"""
import sys
import os

# Set path
sys.path.insert(0, r'C:\Users\perel\OneDrive\Apps\thunderclap-ai')

# Set API key
os.environ['GEMINI_API_KEY'] = 'AIzaSyD-xExhXC66P-eUuYzx5wwXifBvCwZYGMw'

print("Importing QueryEngine...")
from lib.query_engine import QueryEngine

print("Creating QueryEngine (use_async=False for stability)...")
qe = QueryEngine(gemini_api_key=os.environ['GEMINI_API_KEY'], use_async=False)

print("\nRunning query: 'tell me about Lehman'")
print("(Using smaller query to test if it works at all)\n")

try:
    answer = qe.query("tell me about Lehman", use_llm=True)
    print("\n" + "="*70)
    print("SUCCESS! Query worked!")
    print("="*70)
    print(answer[:300] + "...")
except Exception as e:
    print("\n" + "="*70)
    print("ERROR!")
    print("="*70)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

