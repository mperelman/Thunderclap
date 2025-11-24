"""Test detection on chunks that actually have identities"""
import sys
sys.path.insert(0, '.')

from lib.document_parser import load_all_documents
from lib.index_builder import split_into_chunks
from lib.identity_prefilter import IdentityPrefilter
from lib.llm_identity_detector import LLMIdentityDetector

# Load all chunks
docs = load_all_documents(use_cache=True)
all_chunks = []
for doc in docs:
    all_chunks.extend(split_into_chunks(doc['text']))

# Use prefilter to find chunks WITH identities
print("Finding chunks with identity keywords...")
prefilter = IdentityPrefilter()
relevant_indices = prefilter.filter_chunks(all_chunks)
relevant_chunks = [all_chunks[i] for i in relevant_indices]

print(f"  Total chunks: {len(all_chunks)}")
print(f"  Chunks with identities: {len(relevant_chunks)}")
print()

# Test on first 10 chunks that HAVE identities
print("Testing on first 10 chunks with identity keywords...")
print("-" * 70)
sample = relevant_chunks[:10]

print("Sample chunk preview:")
print(sample[0][:200])
print()

detector = LLMIdentityDetector()
results = detector.detect_from_chunks(sample, force_rerun=True)

identities = results.get('identities', {})

print(f"\n[RESULT] Detected {len(identities)} identity types from 10 chunks with keywords")
print()

for identity in sorted(identities.keys())[:15]:
    families = identities[identity]
    print(f"  {identity}: {len(families)} families - {list(families.keys())[:5]}")

if len(identities) > 15:
    print(f"  ... and {len(identities) - 15} more")

if len(identities) >= 5:
    print(f"\n[EXCELLENT] Detector working! Found {len(identities)} identities from 10 chunks")
    print()
    print("Ready to run on ALL 1,292 chunks with identities?")
    response = input("Run full detection? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\nRunning on all 1,292 relevant chunks...")
        print("This will take ~6 minutes with rate limiting...")
        print()
        
        results_full = detector.detect_from_chunks(relevant_chunks, force_rerun=True)
        
        identities_full = results_full.get('identities', {})
        print(f"\n[COMPLETE] Detected {len(identities_full)} identity types!")
        print(f"Total associations: {sum(len(f) for f in identities_full.values())}")
        
        print("\n[NEXT] Rebuild index: python build_index.py")
else:
    print(f"\n[ISSUE] Only found {len(identities)} identities - may need debugging")


