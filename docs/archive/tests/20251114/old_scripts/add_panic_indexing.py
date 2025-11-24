"""
Add Panic Indexing to Existing Index
=====================================
Adds "Panic of YEAR" as specific searchable terms per user instruction.
"""

import sys
sys.path.insert(0, '.')

import json
from lib.panic_indexer import augment_index_with_panics
from lib.document_parser import load_all_documents

print("="*70)
print("ADDING PANIC INDEXING TO INDEX")
print("="*70)
print()

# Load current index
print("Loading current index...")
indices = json.load(open('data/indices.json', encoding='utf-8'))
term_to_chunks = indices['term_to_chunks']

# Load chunks
print("Loading document chunks...")
docs = load_all_documents(use_cache=True)
all_chunks = []
chunk_ids = []

# Recreate chunks to match index
chunk_counter = 0
for doc in docs:
    from lib.query_engine import QueryEngine
    # Use simple chunking
    words = doc['text'].split()
    chunk_size = 500
    overlap = 100
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            all_chunks.append(chunk)
            chunk_ids.append(f"chunk_{chunk_counter}")
            chunk_counter += 1

print(f"  Loaded {len(all_chunks)} chunks")
print()

# Add panic indexing
term_to_chunks = augment_index_with_panics(term_to_chunks, all_chunks, chunk_ids)

# Save updated index
indices['term_to_chunks'] = term_to_chunks
print()
print("Saving updated index...")
with open('data/indices.json', 'w', encoding='utf-8') as f:
    json.dump(indices, f, indent=2, ensure_ascii=False)

print("[OK] Index updated with panic terms")
print()
print("Now you can search:")
print('  ask("tell me about the panic of 1914", use_llm=True)')
print("  → Will find ONLY 1914 panic content, not all panics")

