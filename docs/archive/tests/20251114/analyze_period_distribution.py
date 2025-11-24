"""Analyze actual period distribution in Jewish banker chunks"""
import sys
import re
sys.path.insert(0, '.')

from lib.document_parser import load_all_documents
from lib.index_builder import split_into_chunks
import json

# Load chunks
docs = load_all_documents(use_cache=True)
all_chunks = []
for doc in docs:
    all_chunks.extend(split_into_chunks(doc['text']))

# Load jewish chunks from index
indices = json.load(open('data/indices.json', encoding='utf-8'))
jewish_chunk_ids = indices['term_to_chunks'].get('jewish', [])

# Convert to integers
jewish_chunks = []
for chunk_id in jewish_chunk_ids:
    idx = int(chunk_id.replace('chunk_', ''))
    if idx < len(all_chunks):
        jewish_chunks.append(all_chunks[idx])

print(f'Total Jewish banker chunks: {len(jewish_chunks)}')
print()

# Analyze period distribution
TIME_PERIODS = [
    ("Medieval (800-1499)", r'\b(1[0-4]\d{2}|[89]\d{2})\b'),
    ("16th century", r'\b(15\d{2})\b'),
    ("17th century", r'\b(16\d{2})\b'),
    ("18th century", r'\b(17\d{2})\b'),
    ("19th century", r'\b(18\d{2})\b'),
    ("20th century", r'\b(19\d{2})\b'),
    ("21st century", r'\b(20[012]\d)\b'),
]

period_counts = {name: [] for name, _ in TIME_PERIODS}
period_counts["Undated"] = []

for chunk_id, chunk in enumerate(jewish_chunks):
    found = False
    for period_name, pattern in TIME_PERIODS:
        if re.search(pattern, chunk):
            period_counts[period_name].append(chunk_id)
            found = True
            break
    if not found:
        period_counts["Undated"].append(chunk_id)

print('ACTUAL DISTRIBUTION:')
print('='*60)
for period, chunks in period_counts.items():
    print(f'{period:30s} {len(chunks):4d} chunks')

print()
print('='*60)
print('PROBLEM: System caps at 50 chunks per period!')
print('='*60)
for period, chunks in period_counts.items():
    if len(chunks) > 50:
        print(f'{period:30s} {len(chunks):4d} available → 50 used ({50/len(chunks)*100:.1f}% coverage)')
        print(f'  MISSING: {len(chunks)-50} chunks!')




