"""Test query after waiting"""
import sys
sys.path.insert(0, '.')

from query import ask

print("Querying: Vernon Jordan\n")

result = ask('Vernon Jordan', use_llm=True)

print(f"\nSUCCESS: Generated {len(result)} characters")

with open('temp/vernon_jordan.txt', 'w', encoding='utf-8') as f:
    f.write(result)

print("Saved to temp/vernon_jordan.txt")
print("\nFirst 500 chars:")
print(result[:500])

