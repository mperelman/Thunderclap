"""Force fresh API key load - no caching"""
import sys
import os

# Clear any cached modules
if 'query' in sys.modules:
    del sys.modules['query']
if 'lib.query_engine' in sys.modules:
    del sys.modules['lib.query_engine']
if 'lib.llm' in sys.modules:
    del sys.modules['lib.llm']

sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv(override=True)  # Force reload

key = os.getenv('GEMINI_API_KEY_1')
print(f"Using fresh key: {key[:20]}...")
print()

from query import ask

print("Generating narrative about black bankers...")
print()

try:
    result = ask('black bankers', use_llm=True)
    
    print(f"[SUCCESS] Generated {len(result)} characters\n")
    print("="*60)
    print(result[:1000])
    print("="*60)
    
    with open('temp/black_bankers_success.txt', 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"\n[SAVED] temp/black_bankers_success.txt")

except Exception as e:
    print(f"[ERROR] {e}")

