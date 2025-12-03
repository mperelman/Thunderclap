"""
Heuristic-based term filtering for hyperlinking.
Filters out generic words while keeping proper nouns and specific entities.
"""
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.config import DATA_DIR

# Load the index
indices_file = os.path.join(DATA_DIR, 'indices.json')
with open(indices_file, 'r', encoding='utf-8') as f:
    indices = json.load(f)

term_to_chunks = indices['term_to_chunks']
all_terms = list(term_to_chunks.keys())

print(f"Loaded {len(all_terms)} terms from index")

# Generic words to ALWAYS exclude (even if capitalized or multi-word)
# This includes: generic terms, titles, common place names, descriptors
ALWAYS_EXCLUDE = {
    # Generic financial/business terms
    'financial', 'assets', 'asset', 'son', 'sons', 'daughter', 'daughters',
    'capital', 'credit', 'finance', 'financing', 'investment', 'investments',
    'securities', 'security', 'stock', 'stocks', 'bond', 'bonds',
    'market', 'markets', 'trade', 'trading', 'trader', 'traders',
    'business', 'businesses', 'industry', 'industries', 'sector', 'sectors',
    'economy', 'economic', 'commerce', 'commercial',
    'exchange', 'association', 'society', 'institute', 'foundation',
    'system', 'systems', 'network', 'networks', 'organization', 'organizations',
    'group', 'groups', 'holding', 'holdings', 'corporation', 'corporations',
    
    # Titles and roles (should NOT be hyperlinked)
    'president', 'director', 'chairman', 'officer', 'manager', 'partner',
    'governor', 'mayor', 'senator', 'representative', 'congressman',
    'king', 'queen', 'prince', 'princess', 'duke', 'earl', 'lord', 'lady',
    'emperor', 'czar', 'kaiser', 'sultan', 'shah', 'caliph',
    
    # Family relationships
    'father', 'mother', 'brother', 'sister', 'uncle', 'aunt', 'cousin',
    'wife', 'husband', 'widow', 'widower', 'family', 'families',
    
    # Government/legal terms
    'government', 'federal', 'state', 'national', 'international',
    'public', 'private', 'royal', 'imperial', 'central',
    'board', 'committee', 'commission', 'agency', 'department',
    'act', 'acts', 'law', 'laws', 'rule', 'rules', 'regulation', 'regulations',
    'section', 'sections', 'article', 'articles', 'chapter', 'chapters',
    'policy', 'policies', 'program', 'programs',
    
    # Economic events
    'crisis', 'crises', 'panic', 'panics', 'depression', 'recession',
    'war', 'wars', 'peace', 'treaty', 'treaties', 'agreement', 'agreements',
    
    # Time periods
    'century', 'decade', 'year', 'years', 'period', 'era', 'age',
    'early', 'late', 'mid', 'modern', 'contemporary', 'historical',
    
    # Ordinals and descriptors
    'first', 'second', 'third', 'fourth', 'fifth', 'last', 'final',
    'new', 'old', 'young', 'great', 'grand', 'major', 'minor',
    
    # Directions and regions (generic)
    'north', 'south', 'east', 'west', 'central', 'western', 'eastern',
    'northern', 'southern', 'northeastern', 'northwestern', 'southeastern', 'southwestern',
    'european', 'asian', 'african', 'american', 'british', 'french', 'german',
    
    # Generic place terms
    'city', 'cities', 'town', 'towns', 'village', 'villages',
    'street', 'avenue', 'road', 'boulevard', 'square', 'place',
    'building', 'buildings', 'house', 'houses', 'office', 'offices',
    
    # Major generic place names (too generic to hyperlink)
    'york', 'new york', 'london', 'paris', 'berlin', 'vienna', 'rome',
    'amsterdam', 'brussels', 'geneva', 'zurich', 'madrid', 'lisbon',
    'america', 'europe', 'asia', 'africa', 'australia',
}

filtered_terms = []

for term in all_terms:
    term_lower = term.lower()
    
    # Always exclude generic words (single or multi-word)
    if term_lower in ALWAYS_EXCLUDE:
        continue
    
    # Keep acronyms (3+ caps)
    if term.isupper() and len(term) >= 3:
        filtered_terms.append(term)
        continue
    
    # Keep multi-word terms UNLESS they're generic
    # Check if any word in the term is in the exclusion list
    if ' ' in term:
        # Don't exclude if it's a specific entity with a generic word
        # e.g., "Deutsche Bank" is OK even though "bank" is generic
        # But "New York" is generic even though it's multi-word
        words = term_lower.split()
        # If ALL words are generic, exclude
        if all(w in ALWAYS_EXCLUDE for w in words):
            continue
        # Special case: if it's ONLY place names, exclude
        place_only = all(w in ['york', 'new', 'london', 'paris', 'berlin', 'vienna', 'rome', 
                                'amsterdam', 'brussels', 'geneva', 'zurich', 'madrid', 'lisbon',
                                'america', 'europe', 'asia', 'africa', 'north', 'south', 'east', 'west'] 
                         for w in words)
        if place_only:
            continue
        filtered_terms.append(term)
        continue
    
    # Keep capitalized single words that are likely proper nouns
    # (surnames, firm names, place names)
    if len(term) > 0 and term[0].isupper() and len(term) > 2:
        filtered_terms.append(term)
        continue
    
    # Keep lowercase terms that are NOT generic English words
    # (these are likely specialized terms, foreign words, or technical terms)
    # But skip very short terms (likely generic)
    if len(term) > 4 and not term_lower in ALWAYS_EXCLUDE:
        filtered_terms.append(term)

print(f"\nFiltered: {len(filtered_terms)} terms kept, {len(all_terms) - len(filtered_terms)} removed")
print(f"Removal rate: {((len(all_terms) - len(filtered_terms)) / len(all_terms) * 100):.1f}%")

# Save to lib/filtered_terms.json (used by server)
output_file = os.path.join('lib', 'filtered_terms.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(sorted(filtered_terms), f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved filtered terms to {output_file}")

# Show some examples of what was kept vs removed
print("\n" + "=" * 80)
print("SAMPLE OF KEPT TERMS:")
print("=" * 80)
kept_sample = sorted(filtered_terms)[:30]
for t in kept_sample:
    print(f"  {t}")

print("\n" + "=" * 80)
print("SAMPLE OF REMOVED TERMS:")
print("=" * 80)
removed = [t for t in all_terms if t not in filtered_terms]
removed_sample = sorted(removed)[:30]
for t in removed_sample:
    print(f"  {t}")
