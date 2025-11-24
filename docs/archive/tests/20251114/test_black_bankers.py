"""Test black bankers query"""
import sys
sys.path.insert(0, '.')

from query import ask

print("Querying: black bankers\n")

try:
    result = ask('black bankers', use_llm=True)
    
    print(f"[SUCCESS] Generated {len(result)} characters\n")
    print("="*60)
    print(result[:1000])  # First 1000 chars
    print("="*60)
    
    # Save full result
    with open('temp/black_bankers_full.txt', 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"\n[SAVED] temp/black_bankers_full.txt")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

