"""Test with fresh API keys #5 and #6"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.document_parser import load_all_documents
from lib.index_builder import split_into_chunks
from lib.llm_identity_detector import LLMIdentityDetector

# Load chunks
print("Loading chunks...")
documents = load_all_documents(use_cache=True)
all_chunks = []
for doc in documents:
    chunks = split_into_chunks(doc['text'])
    all_chunks.extend(chunks)

# Find ONE chunk with "Lebanese Christians fleeing"
test_chunk = None
for chunk in all_chunks:
    if 'lebanese christians fleeing' in chunk.lower():
        test_chunk = chunk
        break

if not test_chunk:
    print("Test chunk not found!")
    sys.exit(1)

print(f"Found test chunk (length: {len(test_chunk)} chars)")
print(f"Preview: {test_chunk[:200]}...")

# Test LLM
print("\n[TESTING] LLM on single chunk (should detect: Abdelnour, Boutros, Chammah, Bitar, Jabre)")
detector = LLMIdentityDetector()

# Mark first 4 keys as exhausted, start with key #5
detector.key_manager.failed_keys = {0, 1, 2, 3}
detector.key_manager.current_index = 4

print(f"Using key #{detector.key_manager.current_index + 1}")
print(f"Remaining capacity: {detector.key_manager.get_remaining_capacity()} requests")

# Process single chunk
results = detector.detect_from_chunks([test_chunk], force_rerun=True)

print("\n[RESULTS]")
lebanese = results['identities'].get('lebanese', {})
families = lebanese.get('families', [])
print(f"Lebanese detected: {families}")

if any(name in str(families).lower() for name in ['abdelnour', 'boutros', 'chammah']):
    print("[SUCCESS] LLM found Wall Street Lebanese!")
else:
    print("[FAIL] LLM missed Wall Street Lebanese")

