"""Run Steps 3-4: Surname search and indexing"""
import sys
import re
import json
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, '.')

from lib.document_parser import load_all_documents
from lib.index_builder import split_into_chunks
from lib.identity_hierarchy import get_parent_categories

print("="*70)
print("STEPS 3-4: Surname Search + Index Integration")
print("="*70)
print()

# Load all chunks
print("Loading chunks...")
docs = load_all_documents(use_cache=True)
all_chunks = []
for doc in docs:
    all_chunks.extend(split_into_chunks(doc['text']))

print(f"  Total chunks: {len(all_chunks)}")
print()

# Load LLM results
print("STEP 3: Surname Search Across ALL Chunks")
print("-" * 70)

cache = json.load(open('data/llm_identity_cache.json', encoding='utf-8'))

# Extract surname -> identities mapping
surname_to_identity = defaultdict(set)

for chunk_hash, data in cache.items():
    if data.get('prompt_version') == 'v2' and data.get('identities'):
        for identity, surnames in data.get('identities', {}).items():
            for surname in surnames:
                surname_to_identity[surname.lower()].add(identity)

print(f"  Extracted {len(surname_to_identity)} unique surnames from LLM")
print(f"  Example surnames: {list(surname_to_identity.keys())[:10]}")
print()

# Search for each surname across ALL chunks
print(f"  Searching all {len(all_chunks)} chunks for these surnames...")

surname_to_chunks = defaultdict(set)

for surname in surname_to_identity.keys():
    # Create regex pattern
    pattern = rf'\b{re.escape(surname)}\b'
    compiled = re.compile(pattern, re.IGNORECASE)
    
    for chunk_id, chunk in enumerate(all_chunks):
        if compiled.search(chunk):
            surname_to_chunks[surname].add(chunk_id)

total_matches = sum(len(chunks) for chunks in surname_to_chunks.values())
print(f"  Found {total_matches} total surname occurrences")
print(f"  Average {total_matches/len(surname_to_identity):.1f} chunks per surname")
print()

# STEP 4: Build index
print("STEP 4: Building Index (identity -> chunks)")
print("-" * 70)

identity_to_chunks = defaultdict(set)

for surname, chunk_ids in surname_to_chunks.items():
    identities = surname_to_identity.get(surname, set())
    
    for identity in identities:
        identity_to_chunks[identity].update(chunk_ids)
        
        # Add to parent categories via hierarchy
        parents = get_parent_categories(identity)
        for parent in parents:
            identity_to_chunks[parent].update(chunk_ids)

# Show results
print(f"  Indexed {len(identity_to_chunks)} searchable identities")
print()

for identity in sorted(identity_to_chunks.keys())[:20]:
    count = len(identity_to_chunks[identity])
    print(f"  {identity:20} {count:4} chunks")

if len(identity_to_chunks) > 20:
    print(f"  ... and {len(identity_to_chunks) - 20} more")

# Save results
results = {
    'identities': {
        identity: {
            'chunk_ids': sorted(list(chunk_ids)),
            'chunk_count': len(chunk_ids)
        }
        for identity, chunk_ids in identity_to_chunks.items()
    },
    'surname_to_identity': {s: list(ids) for s, ids in surname_to_identity.items()},
    'stats': {
        'total_chunks': len(all_chunks),
        'unique_surnames': len(surname_to_identity),
        'identity_types': len(identity_to_chunks),
        'total_surname_occurrences': total_matches
    }
}

output_file = Path('data/identity_detection_v3.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print()
print("="*70)
print("[COMPLETE] 4-Step Detection Finished!")
print("="*70)
print(f"  Detected: {len(identity_to_chunks)} identity types")
print(f"  Surnames: {len(surname_to_identity)}")
print(f"  Saved: {output_file}")
print()
print("[NEXT] Rebuild index to integrate:")
print("  python build_index.py")


