"""Find chunks with actual identity detections"""
import json
from collections import defaultdict

with open('data/llm_identity_cache.json', encoding='utf-8') as f:
    cache = json.load(f)

print(f"Total chunks in cache: {len(cache)}")

# Find chunks with identities
chunks_with_identities = 0
all_identities = defaultdict(set)

for chunk_hash, data in cache.items():
    identities = data.get('identities', {})
    if identities:
        chunks_with_identities += 1
        for identity, surnames in identities.items():
            for surname in surnames:
                all_identities[identity].add(surname.lower())

print(f"Chunks with identities: {chunks_with_identities}")
print(f"Chunks without identities: {len(cache) - chunks_with_identities}")
print()

if all_identities:
    print("="*70)
    print("DETECTED IDENTITIES")
    print("="*70)
    print()
    
    for identity in sorted(all_identities.keys()):
        families = sorted(list(all_identities[identity]))
        print(f"{identity}: {len(families)} families")
        print(f"  Examples: {', '.join(families[:10])}")
        print()
    
    print("="*70)
    print(f"TOTAL: {len(all_identities)} identity types")
    print(f"TOTAL: {sum(len(f) for f in all_identities.values())} family detections")
else:
    print("\n[INFO] No identities detected in cache")
    print("This might be because:")
    print("  1. The LLM detector hasn't run yet")
    print("  2. The detector ran but found no identities")
    print("  3. The cache needs to be rebuilt")
    print("\nRun: python lib/llm_identity_detector.py")


