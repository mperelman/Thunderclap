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
    # Check for v2 or v3 prompt versions
    prompt_version = data.get('prompt_version', '')
    if prompt_version in ['v2', 'v3'] and data.get('identities'):
        for identity, surnames in data.get('identities', {}).items():
            for surname in surnames:
                surname_to_identity[surname.lower()].add(identity)

print(f"  Extracted {len(surname_to_identity)} unique surnames from LLM")
print(f"  Example surnames: {list(surname_to_identity.keys())[:10]}")
print()

# AUGMENT with keyword-based LGBTQ+ detection (non-LLM, uses regex patterns)
# NOTE: Keyword detection returns FULL NAMES, not surnames. 
# CRITICAL: LGBTQ+ identity is NAME-BASED, not surname-based. We should NOT tag
# all people with a surname just because one individual with that surname is LGBTQ+.
# 
# Strategy: Only add surnames from keyword detection if they're NOT already in LLM results.
# This is conservative - if LLM didn't catch it, it's likely a specific individual mention
# that keyword detection found. If LLM already has the surname, we trust LLM's context awareness.
print("  Augmenting with keyword-based LGBTQ+ detection...")
try:
    from lib.keyword_lgbtq_detector import KeywordLGBTQDetector
    keyword_detector = KeywordLGBTQDetector()
    keyword_results = keyword_detector.detect_from_chunks(all_chunks)
    
    # Extract surnames from full names
    # Only add if surname is NOT already in LLM results (conservative approach)
    keyword_added = 0
    keyword_skipped = 0
    
    for identity, full_names in keyword_results.items():
        for full_name in full_names:
            # Extract surname (last word of full name)
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                surname = name_parts[-1].lower()
                
                # Only add if this surname is NOT already in LLM results
                # This prevents tagging all people with that surname when only specific individuals are LGBTQ+
                if surname not in surname_to_identity:
                    surname_to_identity[surname].add(identity)
                    keyword_added += 1
                else:
                    # Surname already in LLM results - skip to avoid false positives
                    keyword_skipped += 1
    
    print(f"  Added {keyword_added} keyword-based LGBTQ+ associations (new surnames only)")
    print(f"  Skipped {keyword_skipped} associations (surnames already in LLM results)")
except Exception as e:
    print(f"  [WARN] Keyword detection failed: {e}")
    import traceback
    traceback.print_exc()

print(f"  Total unique surnames after augmentation: {len(surname_to_identity)}")
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


