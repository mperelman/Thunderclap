"""Test script to check what chunks are retrieved for Vienna Rothschild and what years they contain."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.query_engine import QueryEngine
import re

# Initialize query engine
engine = QueryEngine(use_async=False)

# Test query
question = "Tell me about Vienna Rothschild banking"

# Extract keywords manually (similar to what query method does)
import re
stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
              'of', 'with', 'by', 'from', 'about', 'what', 'when', 'where', 'who',
              'why', 'how', 'did', 'do', 'does', 'was', 'were', 'is', 'are', 'tell', 'me'}
raw_tokens = re.findall(r"[A-Za-z']+", question)
keywords = []
for token in raw_tokens:
    lower = token.lower()
    if lower not in stop_words and len(lower) > 3:
        keywords.append(lower)
    elif token.isupper():
        keywords.append(token)

print(f"Keywords: {keywords}")

# Get subject terms
from lib.term_utils import canonicalize_term
canonical_map = {}
for token in raw_tokens:
    lower = token.lower()
    if lower not in stop_words and len(lower) > 3:
        canonical = canonicalize_term(token)
        if canonical:
            canonical_map.setdefault(canonical, set()).add(lower)

subject_terms, subject_phrases = engine._extract_subject_filters(question, keywords, raw_tokens, canonical_map)
print(f"Subject terms: {subject_terms}")
print(f"Subject phrases: {subject_phrases}")

# Search for chunks
chunk_ids = set()
for keyword in keywords:
    if keyword in engine.term_to_chunks:
        chunk_ids.update(engine.term_to_chunks[keyword])

print(f"\nTotal chunk IDs found: {len(chunk_ids)}")

# Fetch chunks
chunk_ids_list = list(chunk_ids)
data = engine.collection.get(ids=chunk_ids_list)

# Analyze chunks by year
chunks_by_year = {}
all_years = set()

for text, meta in zip(data['documents'], data['metadatas']):
    # Extract years
    matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
    years = [int(m) for m in matches]
    if years:
        latest_year = max(years)
        all_years.add(latest_year)
        decade = (latest_year // 10) * 10
        if decade not in chunks_by_year:
            chunks_by_year[decade] = []
        chunks_by_year[decade].append((latest_year, text[:100]))

print(f"\nYears found in chunks: {sorted(all_years)}")
print(f"Latest year: {max(all_years) if all_years else 'None'}")

print(f"\nChunks by decade:")
for decade in sorted(chunks_by_year.keys()):
    print(f"  {decade}s: {len(chunks_by_year[decade])} chunks (latest year: {max(y[0] for y in chunks_by_year[decade])})")

# Check if chunks mention Vienna and Rothschild
vienna_rothschild_chunks = []
for text, meta in zip(data['documents'], data['metadatas']):
    text_lower = text.lower()
    has_vienna = "vienna" in text_lower
    has_rothschild = "rothschild" in text_lower
    if has_vienna and has_rothschild:
        matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
        years = [int(m) for m in matches] if matches else []
        latest = max(years) if years else 0
        vienna_rothschild_chunks.append((latest, text[:150]))

print(f"\nChunks mentioning both 'Vienna' and 'Rothschild': {len(vienna_rothschild_chunks)}")
if vienna_rothschild_chunks:
    latest_vr = max(y[0] for y in vienna_rothschild_chunks)
    print(f"Latest year in Vienna+Rothschild chunks: {latest_vr}")
    print(f"\nSample chunks with latest years:")
    for year, text in sorted(vienna_rothschild_chunks, key=lambda x: x[0], reverse=True)[:5]:
        print(f"  {year}: {text}...")

