"""Test script to check what years are in Vienna Rothschild chunks."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
import re

# Direct config values to avoid import issues
VECTORDB_DIR = "vectordb"
COLLECTION_NAME = "thunderclap_chunks"

# Connect to ChromaDB
chroma_client = chromadb.PersistentClient(path=VECTORDB_DIR)
collection = chroma_client.get_collection(name=COLLECTION_NAME)

# Search for Vienna Rothschild
results = collection.get(
    where={"$or": [
        {"body_terms": {"$contains": "vienna"}},
        {"body_terms": {"$contains": "rothschild"}}
    ]},
    limit=200
)

# Extract all years
all_years = set()
for text in results['documents']:
    matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
    all_years.update(int(m) for m in matches)

years_sorted = sorted(all_years)
print(f"Total chunks: {len(results['documents'])}")
print(f"Years found: {years_sorted}")
print(f"Latest year: {max(years_sorted) if years_sorted else 'None'}")
print(f"Years >= 1900: {[y for y in years_sorted if y >= 1900]}")

