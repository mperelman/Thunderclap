"""
Filter indexed terms using heuristics to identify only meaningful entities.
This removes generic words and keeps only proper nouns, specific entities, and meaningful terms.
"""
import sys
import os
sys.path.insert(0, '.')

import json

print("="*80)
print("FILTERING INDEXED TERMS (HEURISTIC)")
print("="*80)
print()

# Load current index
print("1. Loading current index...")
from lib.config import INDICES_FILE
with open(INDICES_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

terms = list(data.get('term_to_chunks', {}).keys())
term_to_chunks = data.get('term_to_chunks', {})
total_chunks = sum(len(chunks) for chunks in term_to_chunks.values()) if term_to_chunks else 1

print(f"   Total terms in index: {len(terms)}")
print()

# Apply heuristic filtering
print("2. Applying heuristic filters...")
filtered_terms = []

for term in terms:
    term_lower = term.lower().strip()
    
    # Rule 1: Skip if too short
    if len(term) < 4:
        continue
    
    # Rule 2: Skip if it's just a number
    if term_lower.isdigit():
        continue
    
    # Rule 3: Skip if it's a single character repeated
    if len(set(term_lower)) == 1:
        continue
    
    # Rule 4: Skip if term appears in too many chunks (>10% = too generic)
    chunk_count = len(term_to_chunks.get(term, []))
    if chunk_count > max(50, total_chunks * 0.1):
        continue
    
    # Rule 5: ONLY include terms that look like entities:
    
    # 5a. Multi-word phrases (likely entity names)
    if ' ' in term:
        # Skip generic phrases like "and the", "of the"
        words = term_lower.split()
        if len(words) >= 2 and any(len(w) >= 4 for w in words):
            filtered_terms.append(term)
        continue
    
    # 5b. Proper nouns (capitalized) - these are likely names
    if term[0].isupper():
        filtered_terms.append(term)
        continue
    
    # 5c. Acronyms (all caps, 2+ chars)
    if term.isupper() and len(term) >= 2:
        filtered_terms.append(term)
        continue
    
    # 5d. Mixed case (e.g., "iPhone", "McDonald")
    if any(c.isupper() for c in term[1:]):
        filtered_terms.append(term)
        continue
    
    # 5e. Lowercase terms: ONLY if they're identity terms or very specific
    # Identity terms from .cursorrules
    identity_keywords = {
        'jewish', 'jew', 'jews', 'sephardi', 'sephardim', 'ashkenazi', 'ashkenazim',
        'quaker', 'quakers', 'huguenot', 'huguenots', 'mennonite', 'mennonites',
        'puritan', 'puritans', 'protestant', 'catholic', 'muslim', 'muslims',
        'parsee', 'parsees', 'armenian', 'armenians', 'greek', 'greeks',
        'black', 'african', 'latino', 'latina', 'hispanic',
        'female', 'woman', 'women', 'widow', 'widows', 'daughter', 'daughters',
        'queen', 'princess', 'duchess', 'countess', 'baroness',
        'kohanim', 'katz', 'levite', 'levites',
    }
    if term_lower in identity_keywords:
        filtered_terms.append(term)
        continue
    
    # 5f. Panic terms (e.g., "panic of 1929", "panic_of_1929")
    if 'panic' in term_lower or 'crisis' in term_lower:
        if any(c.isdigit() for c in term):  # Contains a year
            filtered_terms.append(term)
            continue
    
    # 5g. Law codes (e.g., "ba1933", "ta1813")
    if len(term) >= 6 and term[:2].isalpha() and term[2:6].isdigit():
        filtered_terms.append(term)
        continue
    
    # Everything else is excluded (lowercase generic words)

print()
print(f"3. Filtering complete!")
print(f"   Original terms: {len(terms)}")
print(f"   Filtered terms: {len(filtered_terms)}")
print(f"   Removed: {len(terms) - len(filtered_terms)} ({100*(len(terms) - len(filtered_terms))/len(terms):.1f}%)")
print()

# Save filtered terms list
output_file = 'data/filtered_terms.json'
print(f"4. Saving filtered terms to {output_file}...")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(sorted(set(filtered_terms)), f, indent=2, ensure_ascii=False)

print()
print("="*80)
print("DONE!")
print("="*80)
print()
print("Filtered terms saved. server.py will now load this file for hyperlinking.")

