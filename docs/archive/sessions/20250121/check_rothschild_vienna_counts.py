"""Check index counts for Rothschild and Vienna terms."""
import sys
import json
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.config import INDICES_FILE

# Load the index
if not os.path.exists(INDICES_FILE):
    print(f"Index file not found: {INDICES_FILE}")
    exit(1)

with open(INDICES_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

term_to_chunks = data.get('term_to_chunks', {})

# Check various term variations
terms_to_check = [
    'rothschild',
    'vienna',
    'rothschild vienna',  # phrase
    'vienna rothschild',  # reverse phrase
]

print("=" * 60)
print("INDEX COUNTS FOR ROTHSCHILD AND VIENNA")
print("=" * 60)

# Individual terms
rothschild_chunks = set(term_to_chunks.get('rothschild', []))
vienna_chunks = set(term_to_chunks.get('vienna', []))

print(f"\n1. 'rothschild' (individual term):")
print(f"   Chunks: {len(rothschild_chunks)}")

print(f"\n2. 'vienna' (individual term):")
print(f"   Chunks: {len(vienna_chunks)}")

# Intersection
intersection = rothschild_chunks & vienna_chunks
print(f"\n3. Intersection (both 'rothschild' AND 'vienna'):")
print(f"   Chunks: {len(intersection)}")

# Union
union = rothschild_chunks | vienna_chunks
print(f"\n4. Union (either 'rothschild' OR 'vienna'):")
print(f"   Chunks: {len(union)}")

# Check for phrase indexing
print(f"\n5. Phrase checks:")
for phrase in ['rothschild vienna', 'vienna rothschild']:
    phrase_chunks = term_to_chunks.get(phrase, [])
    if phrase_chunks:
        print(f"   '{phrase}' (as phrase): {len(phrase_chunks)} chunks")
    else:
        print(f"   '{phrase}' (as phrase): NOT INDEXED")

# Check for other variations
print(f"\n6. Other variations in index:")
all_terms = list(term_to_chunks.keys())
rothschild_terms = [t for t in all_terms if 'rothschild' in t.lower()]
vienna_terms = [t for t in all_terms if 'vienna' in t.lower()]

if rothschild_terms:
    print(f"   Terms containing 'rothschild': {len(rothschild_terms)}")
    for term in sorted(rothschild_terms)[:10]:  # Show first 10
        print(f"      - '{term}': {len(term_to_chunks[term])} chunks")
    if len(rothschild_terms) > 10:
        print(f"      ... and {len(rothschild_terms) - 10} more")

if vienna_terms:
    print(f"\n   Terms containing 'vienna': {len(vienna_terms)}")
    for term in sorted(vienna_terms)[:10]:  # Show first 10
        print(f"      - '{term}': {len(term_to_chunks[term])} chunks")
    if len(vienna_terms) > 10:
        print(f"      ... and {len(vienna_terms) - 10} more")

print("\n" + "=" * 60)
print("SUMMARY:")
print(f"  - 'rothschild' only: {len(rothschild_chunks - vienna_chunks)} chunks")
print(f"  - 'vienna' only: {len(vienna_chunks - rothschild_chunks)} chunks")
print(f"  - Both terms: {len(intersection)} chunks")
print("=" * 60)

