import json

# Load index
indices = json.load(open('data/indices.json', encoding='utf-8'))

# Get chunks
hindu_chunks = set(indices['term_to_chunks'].get('hindu', []))
dalit_chunks = set(indices['term_to_chunks'].get('dalit', []))

print("CHUNK OVERLAP ANALYSIS")
print("="*60)
print()
print(f"Chunks about 'hindu': {len(hindu_chunks)}")
print(f"Chunks about 'dalit': {len(dalit_chunks)}")
print()
print(f"Overlap (chunks containing BOTH): {len(hindu_chunks & dalit_chunks)}")
print(f"Hindu-only (no dalit mention): {len(hindu_chunks - dalit_chunks)}")
print(f"Dalit-only (no hindu mention): {len(dalit_chunks - hindu_chunks)}")
print()
print("="*60)
print("THE PROBLEM")
print("="*60)
print()
print("When you search 'hindus', the system finds Hindu chunks.")
print("But Dalit content might be in SEPARATE chunks!")
print()
print("If dalit_chunks don't overlap with hindu_chunks,")
print("then a 'hindu' query will MISS all the Dalit content.")
print()
print("This is why the narrative:")
print("  ✓ Mentions Cisco 2020 case (probably from a chunk tagged 'hindu' AND 'dalit')")
print("  ✗ Misses EIC-Dalit military service (probably in 'dalit' chunk without 'hindu' tag)")




