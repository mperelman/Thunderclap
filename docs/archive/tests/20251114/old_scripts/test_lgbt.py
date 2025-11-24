"""Test LGBT detection on Raphael Bostic"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from lib.identity_detector import IdentityDetector
from lib.index_builder import split_into_chunks

# Load document
text = json.load(open('data/cache/Thunderclap Part III.docx.cache.json'))['text']

# Find chunks with Bostic
chunks = split_into_chunks(text)
bostic_chunks = [c for c in chunks if 'Bostic' in c]

print(f"Chunks containing 'Bostic': {len(bostic_chunks)}")
print(f"\nChunk preview (first 300 chars):")
print(bostic_chunks[0][:300] if bostic_chunks else "None")

# Test if 'openly gay' is found in chunk
test_chunk = bostic_chunks[0] if bostic_chunks else ""
test_lower = test_chunk.lower()
print(f"\nChecking identity term presence:")
print(f"  'gay' in chunk? {'gay' in test_lower}")
print(f"  'openly gay' in chunk? {'openly gay' in test_lower}")
print(f"  'lesbian' in chunk? {'lesbian' in test_lower}")

# Run detector on these specific chunks
print(f"\n{'='*60}")
print("Running detector...")
detector = IdentityDetector()
results = detector.extract_from_documents(bostic_chunks)

# Show RAW counts before filtering
print(f"\nRAW LGBT counts (before >= 3 filter):")
print(f"  {dict(detector.identity_families.get('lgbt', {}))}")

# Show LGBT results
lgbt_data = results.get('identities', {}).get('lgbt', {})
if lgbt_data:
    individuals = lgbt_data.get('individuals', [])
    print(f"\n[OK] LGBT individuals found: {individuals}")
    print(f"  Counts: {lgbt_data.get('counts', {})}")
    print(f"  Type: {lgbt_data.get('type', 'N/A')}")
else:
    print("\n[FAIL] No LGBT families detected")
    print("\nDEBUG: Checking if 'openly gay' is in chunk...")
    for chunk in bostic_chunks:
        if 'openly gay' in chunk.lower():
            print("  [OK] Found 'openly gay' in chunk")
            # Test pattern manually
            import re
            pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+became\s+the\s+first.{0,50}?openly\s+(?:gay|lesbian)'
            match = re.search(pattern, chunk)
            if match:
                print(f"  [OK] Pattern matches: {match.group(1)}")
            else:
                print("  [FAIL] Pattern doesn't match")
                print(f"  Chunk excerpt: {chunk[chunk.lower().find('bostic')-50:chunk.lower().find('bostic')+150]}")

