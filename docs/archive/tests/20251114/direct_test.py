"""Direct test of query engine with async disabled"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.query_engine import QueryEngine

# Set API key
os.environ['GEMINI_API_KEY'] = 'AIzaSyAztOHisWFGmAxxuTyuvUTwPzKI4cgrH24'

print("Creating QueryEngine with use_async=False...")
qe = QueryEngine(gemini_api_key=os.environ['GEMINI_API_KEY'], use_async=False)

print("\nTesting query: 'tell me about female bankers'")
print("This will use sequential processing (slower but stable)...\n")

try:
    answer = qe.query("tell me about female bankers", use_llm=True)
    print("\n" + "="*70)
    print("SUCCESS!")
    print("="*70)
    print(answer[:500])
    print("\n[... truncated for display ...]")
except Exception as e:
    print("\n" + "="*70)
    print("ERROR!")
    print("="*70)
    import traceback
    traceback.print_exc()

