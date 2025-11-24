import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.config import INDICES_FILE

data = json.load(open(INDICES_FILE))
keys = list(data['term_to_chunks'].keys())

# Find all Rothschild location phrases
rothschild_phrases = [k for k in keys if k.startswith('rothschild ') and len(k.split()) == 2]
print('Rothschild location phrases in index:')
for p in sorted(rothschild_phrases):
    print(f'  {p}: {len(data["term_to_chunks"][p])} chunks')

# Find all Lazard location phrases
lazard_phrases = [k for k in keys if k.startswith('lazard ') and len(k.split()) == 2]
print('\nLazard location phrases in index:')
for p in sorted(lazard_phrases):
    print(f'  {p}: {len(data["term_to_chunks"][p])} chunks')

