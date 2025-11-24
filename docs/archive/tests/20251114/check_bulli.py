import json

# Load index
with open('data/indices.json', encoding='utf-8') as f:
    idx = json.load(f)

# Search for bulli
terms = [t for t in idx['term_to_chunks'].keys() if 'bulli' in t.lower()]

print(f"Terms containing 'bulli': {len(terms)}")
print()

if terms:
    for t in sorted(terms)[:20]:
        chunks = idx['term_to_chunks'][t]
        print(f"  - '{t}': {len(chunks)} chunks")
else:
    print("  No terms found containing 'bulli'")
    print()
    print("Checking similar terms...")
    similar = [t for t in idx['term_to_chunks'].keys() if 'bull' in t.lower()]
    print(f"  Terms containing 'bull': {len(similar)}")
    for t in sorted(similar)[:10]:
        print(f"    - '{t}'")



