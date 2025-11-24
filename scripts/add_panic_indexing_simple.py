"""Add Panic Indexing - Simple Version"""
import sys
sys.path.insert(0, '.')

import json
import re
import chromadb

print("="*70)
print("ADDING PANIC INDEXING")
print("="*70)
print()

# Load current index
print("1. Loading current index...")
indices = json.load(open('data/indices.json', encoding='utf-8'))
term_to_chunks = indices['term_to_chunks']
print(f"   Current terms: {len(term_to_chunks)}")

# Load chunks from vectordb
print("2. Loading chunks from database...")
from lib.config import VECTORDB_DIR, COLLECTION_NAME

client = chromadb.PersistentClient(path=VECTORDB_DIR)
collection = client.get_collection(name=COLLECTION_NAME)

# Get ALL chunks
all_data = collection.get()
chunks = all_data['documents']
chunk_ids = all_data['ids']

print(f"   Loaded {len(chunks)} chunks")
print()

# Index panics
print("3. Scanning for specific panics...")
KNOWN_PANICS = [
    1763, 1772, 1792, 1797, 1810, 1819, 1825, 1837, 1847, 1857, 
    1866, 1873, 1884, 1890, 1893, 1896, 1901, 1907, 1914, 1920,
    1929, 1931, 1933, 1937, 1987, 1989, 1997, 1998, 2000, 2001, 2007, 2008
]

panics_found = 0

for year in KNOWN_PANICS:
    panic_pattern = rf'\b[Pp]anic\s+of\s+{year}\b'
    crisis_pattern = rf'\b[Cc]risis\s+of\s+{year}\b'
    
    matching_chunks = []
    
    for chunk_id, chunk_text in zip(chunk_ids, chunks):
        if re.search(panic_pattern, chunk_text) or re.search(crisis_pattern, chunk_text):
            matching_chunks.append(chunk_id)
    
    if matching_chunks:
        # Index with spaces for natural search
        term = f'panic of {year}'
        term_to_chunks[term] = matching_chunks
        print(f"   {term}: {len(matching_chunks)} chunks")
        panics_found += 1

print()
print(f"4. Indexed {panics_found} specific panics")
print()

# Save updated index
print("5. Saving updated index...")
indices['term_to_chunks'] = term_to_chunks
with open('data/indices.json', 'w', encoding='utf-8') as f:
    json.dump(indices, f, indent=2, ensure_ascii=False)

print(f"[OK] Index updated: {len(term_to_chunks)} total terms")
print()
print("Now you can search:")
print('  ask("tell me about the panic of 1914", use_llm=True)')
print("  → Finds ONLY 1914-specific content")






