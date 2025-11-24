"""Test LLM detection on small sample"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.document_parser import load_all_documents
from lib.index_builder import split_into_chunks
from lib.llm_identity_detector import LLMIdentityDetector
from dotenv import load_dotenv

load_dotenv()

# Load documents
print("Loading documents...")
documents = load_all_documents(use_cache=True)
all_chunks = []
for doc in documents:
    chunks = split_into_chunks(doc['text'])
    all_chunks.extend(chunks)

# Find chunks with specific content
print("\nSelecting chunks with: Lebanese Christians, Omu Okwei, Dantata, Chavez...")
test_chunks = []
keywords = ['lebanese christians fleeing', 'omu okwei', 'dantata', 'martin chavez', 
            'patricia diaz', 'hausa', 'yoruba', 'bassoco', 'sursock']

for chunk in all_chunks:
    chunk_lower = chunk.lower()
    if any(kw in chunk_lower for kw in keywords):
        test_chunks.append(chunk)
        if len(test_chunks) >= 10:
            break

print(f"Selected {len(test_chunks)} highly relevant chunks")

# Run LLM detector with SMALL batch size
print("\n[RUNNING] LLM detector with batch_size=3...")
print("API calls: ~3-4 calls")

detector = LLMIdentityDetector()
detector.BATCH_SIZE = 3
detector.SECONDS_PER_REQUEST = 5

start = time.time()
results = detector.detect_from_chunks(test_chunks, identities_to_process=None, force_rerun=True)
elapsed = time.time() - start

print(f"\n[COMPLETE] Time: {elapsed:.1f}s")
print(f"\nIdentities detected: {len(results['identities'])}")
print("\nSample results:")
for identity in ['lebanese', 'latino', 'basque', 'black', 'hausa', 'yoruba', 'muslim']:
    data = results['identities'].get(identity, {})
    families = data.get('families', []) or data.get('individuals', [])
    if families:
        print(f"  {identity}: {families[:10]}")

