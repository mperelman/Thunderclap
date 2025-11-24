"""Test Lebanese Wall Street detection"""
import json
import re
from lib.index_builder import split_into_chunks

# Load and chunk text
text = json.load(open('data/cache/Thunderclap Part III.docx.cache.json'))['text']
chunks = split_into_chunks(text)

# Find chunks with Lebanese Christians
lebanese_chunks = [chunk for chunk in chunks if 'lebanese christians' in chunk.lower()]
print(f'Found {len(lebanese_chunks)} chunks with "Lebanese Christians"\n')

for i, chunk in enumerate(lebanese_chunks[:2]):
    print(f'--- Chunk {i+1} ---')
    # Show where Lebanese Christians appears
    idx = chunk.lower().find('lebanese christians')
    print(chunk[idx:idx+600])
    print('\n')
    
    # Test pattern
    pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:sold|became|led|held|was|joined)'
    matches = re.findall(pattern, chunk[idx:idx+600])
    print(f'Names found: {matches}')
    print('='*60 + '\n')

