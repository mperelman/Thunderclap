"""Verify that 'rothschild vienna' phrase is indexed."""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.config import INDICES_FILE

with open(INDICES_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

terms = data['term_to_chunks']
phrase = 'rothschild vienna'

print(f"Checking for phrase: '{phrase}'")
if phrase in terms:
    print(f"  [OK] Found! {len(terms[phrase])} chunks")
else:
    print(f"  [NOT FOUND]")

print(f"\nAll phrases containing both 'rothschild' and 'vienna':")
rothschild_vienna_phrases = [t for t in terms.keys() if 'rothschild' in t.lower() and 'vienna' in t.lower()]
for t in sorted(rothschild_vienna_phrases):
    print(f"  - '{t}': {len(terms[t])} chunks")

