"""Search for exact phrase 'rothschild vienna' in chunks."""
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import chromadb
from lib.config import VECTORDB_DIR, INDICES_FILE
import json

# Load index to find chunks with both terms
with open(INDICES_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

term_to_chunks = data.get('term_to_chunks', {})

# Get chunks that contain both terms
rothschild_chunks = set(term_to_chunks.get('rothschild', []))
vienna_chunks = set(term_to_chunks.get('vienna', []))
intersection = rothschild_chunks & vienna_chunks

print(f"Found {len(intersection)} chunks containing both 'rothschild' and 'vienna'")
print("Searching for exact phrase 'rothschild vienna'...\n")

# Load ChromaDB collection
chroma_client = chromadb.PersistentClient(path=VECTORDB_DIR)
collection = chroma_client.get_collection("historical_documents")

# Get all chunks that contain both terms
chunk_ids_list = list(intersection)
if not chunk_ids_list:
    print("No chunks to search.")
    exit(0)

data = collection.get(ids=chunk_ids_list)

# Search for the phrase (case-insensitive)
# Account for HTML italics: <italic>Rothschild</italic> Vienna or plain Rothschild Vienna
phrase_pattern = re.compile(r'(?:<italic>)?rothschild(?:</italic>)?\s+vienna\b', re.IGNORECASE)
reverse_pattern = re.compile(r'\bvienna\s+(?:<italic>)?rothschild(?:</italic>)?\b', re.IGNORECASE)

# Also check for words within 5 words of each other
close_pattern = re.compile(r'\brothschild\b.*?\bvienna\b', re.IGNORECASE)
close_reverse = re.compile(r'\bvienna\b.*?\brothschild\b', re.IGNORECASE)

total_occurrences = 0
chunks_with_phrase = 0
chunks_with_reverse = 0
chunks_with_close = 0
close_examples = []
examples = []

for chunk_id, text in zip(data['ids'], data['documents']):
    # Count occurrences of "rothschild vienna" (adjacent)
    matches = phrase_pattern.findall(text)
    reverse_matches = reverse_pattern.findall(text)
    
    if matches:
        chunks_with_phrase += 1
        total_occurrences += len(matches)
        # Store first example from this chunk
        if len(examples) < 5:
            # Find context around first match
            match_obj = phrase_pattern.search(text)
            if match_obj:
                start = max(0, match_obj.start() - 100)
                end = min(len(text), match_obj.end() + 100)
                context = text[start:end].replace('\n', ' ')
                examples.append((chunk_id, context))
    
    if reverse_matches:
        chunks_with_reverse += 1
        total_occurrences += len(reverse_matches)
    
    # Check for words within 10 words of each other
    words = text.split()
    rothschild_positions = [i for i, word in enumerate(words) if 'rothschild' in word.lower()]
    vienna_positions = [i for i, word in enumerate(words) if 'vienna' in word.lower()]
    
    # Check if any rothschild is within 10 words of any vienna
    found_close = False
    for r_pos in rothschild_positions:
        for v_pos in vienna_positions:
            if abs(r_pos - v_pos) <= 10:
                found_close = True
                if len(close_examples) < 5:
                    # Get context around these positions
                    start_idx = max(0, min(r_pos, v_pos) - 5)
                    end_idx = min(len(words), max(r_pos, v_pos) + 6)
                    context_words = words[start_idx:end_idx]
                    context = ' '.join(context_words)
                    close_examples.append((chunk_id, context))
                break
        if found_close:
            break
    
    if found_close:
        chunks_with_close += 1

print("=" * 70)
print("PHRASE SEARCH RESULTS")
print("=" * 70)
print(f"\nExact phrase 'rothschild vienna' (case-insensitive):")
print(f"  - Total occurrences: {total_occurrences}")
print(f"  - Chunks containing exact phrase: {chunks_with_phrase}")
print(f"  - Chunks containing 'vienna rothschild': {chunks_with_reverse}")

print(f"\nWords within 10 words of each other:")
print(f"  - Chunks with 'rothschild' and 'vienna' within 10 words: {chunks_with_close}")

if close_examples:
    print(f"\nFirst {len(close_examples)} examples where words appear close together:")
    for i, (chunk_id, context) in enumerate(close_examples, 1):
        print(f"\n  Example {i} (chunk {chunk_id}):")
        print(f"  ...{context}...")

if examples:
    print(f"\nFirst {len(examples)} examples with exact phrase (with context):")
    for i, (chunk_id, context) in enumerate(examples, 1):
        print(f"\n  Example {i} (chunk {chunk_id}):")
        print(f"  ...{context}...")

print("\n" + "=" * 70)
print(f"SUMMARY:")
print(f"  - Chunks with both terms: {len(intersection)}")
print(f"  - Chunks with exact phrase 'rothschild vienna': {chunks_with_phrase}")
print(f"  - Chunks with words within 10 words: {chunks_with_close}")
print(f"  - Total exact phrase occurrences: {total_occurrences}")
print("=" * 70)

