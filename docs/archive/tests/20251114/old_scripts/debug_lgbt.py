"""Debug why lavender marriages aren't being detected"""
import json
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from lib.index_builder import split_into_chunks

# Load Part II (has lavender marriages)
text = json.load(open('data/cache/Thunderclap Part II.docx.cache.json'))['text']
chunks = split_into_chunks(text)

# Find chunks with "lavender"
lavender_chunks = [c for c in chunks if 'lavender' in c.lower()]
print(f"Chunks containing 'lavender': {len(lavender_chunks)}")

if lavender_chunks:
    chunk = lavender_chunks[0]
    print(f"\nChunk preview (first 500 chars):")
    print(chunk[:500])
    
    # Check what the quote character actually is
    idx = chunk.find('lavender')
    if idx > 0:
        char_before = chunk[idx-1]
        char_after = chunk[idx+8]
        print(f"\nQuote before 'lavender': {repr(char_before)} (Unicode: U+{ord(char_before):04X})")
        print(f"Quote after 'lavender': {repr(char_after)} (Unicode: U+{ord(char_after):04X})")
    
    # Test Pattern 13 - with all possible quote characters
    pattern13_fixed = r'([A-Z][a-z]+)(?=.{0,100}lavender)'  # Ignore quotes entirely
    matches = re.findall(pattern13_fixed, chunk)
    print(f"\nPattern 13 matches (ignoring quotes): {matches[:10]}")
    
    # Show where lavender appears
    idx = chunk.lower().find('lavender')
    if idx > 0:
        print(f"\nContext around 'lavender':")
        print(chunk[max(0,idx-150):idx+100])

