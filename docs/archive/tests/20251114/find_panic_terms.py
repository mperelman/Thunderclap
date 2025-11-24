import json

indices = json.load(open('data/indices.json', encoding='utf-8'))
terms = indices['term_to_chunks']

# Find panic-related terms
panic_terms = {k: len(v) for k, v in terms.items() if 'panic' in k.lower()}

print("="*60)
print("CURRENT INDEX: Panic Terms")
print("="*60)
print()

if panic_terms:
    for term in sorted(panic_terms.keys()):
        print(f'{term:30s} {panic_terms[term]:4d} chunks')
else:
    print("NO panic terms found")

print()
print("="*60)
print("WHAT SHOULD BE INDEXED (per user instruction)")
print("="*60)
print()
print("User told you to index:")
print("  'Panic of 1763'")
print("  'Panic of 1825'")
print("  'Panic of 1837'")
print("  'Panic of 1857'")
print("  'Panic of 1873'")
print("  'Panic of 1893'")
print("  'Panic of 1907'")
print("  'Panic of 1914'")
print("  'Panic of 1929'")
print("  etc.")
print()
print("This would allow specific panic searches without getting")
print("ALL panic content from ALL centuries mixed together.")




