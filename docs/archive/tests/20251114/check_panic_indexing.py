import json

indices = json.load(open('data/indices.json', encoding='utf-8'))
terms = indices['term_to_chunks']

# Check specific terms
panic_1914 = terms.get('panic of 1914', [])
panic_1914_alt = terms.get('panic_of_1914', [])
panic = terms.get('panic', [])
year_1914 = terms.get('1914', [])

print("PANIC OF 1914 INDEXING")
print("="*60)
print()
print(f'"panic of 1914" (phrase): {len(panic_1914)} chunks')
print(f'"panic_of_1914" (underscore): {len(panic_1914_alt)} chunks')
print(f'"panic" (word): {len(panic)} chunks')
print(f'"1914" (year): {len(year_1914)} chunks')
print()

# Find all terms with panic or 1914
panic_terms = [k for k in terms.keys() if 'panic' in k.lower()]
year_1914_terms = [k for k in terms.keys() if '1914' in k]

print("Terms containing 'panic':")
for term in sorted(panic_terms)[:10]:
    print(f'  {term}: {len(terms[term])} chunks')

print()
print("Terms containing '1914':")
for term in sorted(year_1914_terms)[:10]:
    print(f'  {term}: {len(terms[term])} chunks')

print()
print("="*60)
print("HOW THE QUERY WORKS")
print("="*60)
print()
print('Query: "tell me about the panic of 1914"')
print('System extracts keywords: ["panic", "1914"]')
print(f'Finds: {len(panic)} chunks with "panic"')
print(f'       {len(year_1914)} chunks with "1914" (if indexed)')
print()
print('Result: 562 chunks found')
print()
print('This includes ALL panic-related content (not just 1914)')
print('Which is why it found Medieval/16th-17th century content!')




