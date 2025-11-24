"""Investigate why LLM detector failed so badly"""
import json
from collections import defaultdict

# Load cache
with open('data/llm_identity_cache.json', encoding='utf-8') as f:
    cache = json.load(f)

print("="*70)
print("INVESTIGATING LLM DETECTOR FAILURE")
print("="*70)
print()

# Find chunks with identities
chunks_with_ids = [(h, d) for h, d in cache.items() if d.get('identities')]
chunks_without = len(cache) - len(chunks_with_ids)

print(f"Total chunks: {len(cache)}")
print(f"Chunks WITH identities: {len(chunks_with_ids)}")
print(f"Chunks WITHOUT identities: {chunks_without}")
print(f"Success rate: {len(chunks_with_ids)/len(cache)*100:.1f}%")
print()

if chunks_with_ids:
    print("="*70)
    print("SUCCESSFUL DETECTIONS (first 5):")
    print("="*70)
    print()
    
    for i, (chunk_hash, data) in enumerate(chunks_with_ids[:5], 1):
        print(f"{i}. Chunk: {chunk_hash[:12]}...")
        print(f"   Preview: {data.get('text_preview', '')[:80]}...")
        print(f"   Identities found: {data.get('identities', {})}")
        print()

print("="*70)
print("CHECKING CANDIDATE EXTRACTION LOGIC")
print("="*70)
print()

# Test the candidate extraction on a sample chunk
sample_text = """
Jewish Rothschild merged with Quaker Barclay in London. 
The Sephardi Sassoon family traded with Parsee Tata in India.
Black banker Richard Parsons joined Citi.
Lebanese Maronite George Boutros worked at CSFB.
"""

print("Sample text:")
print(sample_text)
print()

# Try to extract candidates like the detector does
import re

print("Testing candidate extraction...")
identity_keywords = ['jewish', 'quaker', 'sephardi', 'parsee', 'black', 'lebanese', 'maronite']

for keyword in identity_keywords:
    pattern = rf'\b{keyword}\b[^.]*?\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
    matches = re.findall(pattern, sample_text, re.IGNORECASE)
    if matches:
        print(f"  {keyword}: {matches}")

print()
print("If extraction logic is broken, it would explain 99.7% failure rate!")

