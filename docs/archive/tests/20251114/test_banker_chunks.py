"""Test on chunks that should have banker names"""
import sys
sys.path.insert(0, '.')

from lib.document_parser import load_all_documents
from lib.index_builder import split_into_chunks
from lib.llm_identity_detector import LLMIdentityDetector

# Load chunks
docs = load_all_documents(use_cache=True)
all_chunks = []
for doc in docs:
    all_chunks.extend(split_into_chunks(doc['text']))

# Test chunks 100-110 (should have actual banking content)
sample = all_chunks[100:110]

print("Testing chunks 100-110 (banking content)...")
print(f"Sample preview:\n{sample[0][:300]}\n")
print("-" * 70)

detector = LLMIdentityDetector()
results = detector.detect_from_chunks(sample, force_rerun=True)

identities = results.get('identities', {})

print(f"\n[RESULT] Detected {len(identities)} identity types")
print()

if identities:
    for identity in sorted(identities.keys())[:20]:
        families = identities[identity]
        print(f"  {identity}: {list(families.keys())[:8]}")
else:
    print("No identities detected - checking cache...")
    import json
    cache = json.load(open('data/llm_identity_cache.json', encoding='utf-8'))
    v2_with_ids = [(h, d) for h, d in cache.items() if d.get('prompt_version') == 'v2' and d.get('identities')]
    print(f"  v2 chunks with identities: {len(v2_with_ids)}")
    if v2_with_ids:
        print(f"  Example: {v2_with_ids[0][1]}")


