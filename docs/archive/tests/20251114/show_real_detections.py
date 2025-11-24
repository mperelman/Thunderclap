"""Show real detected families from the cache"""
import json
from collections import defaultdict

# Load the LLM identity cache (has the real data)
cache_file = 'data/llm_identity_cache.json'

with open(cache_file, encoding='utf-8') as f:
    cache = json.load(f)

print("="*70)
print("IDENTITIES DETECTED IN YOUR DOCUMENTS (from LLM cache)")
print("="*70)
print(f"Total chunks processed: {len(cache)}")
print()

# Aggregate identities from cache
identities = defaultdict(set)

for chunk_hash, data in cache.items():
    chunk_identities = data.get('identities', {})
    for identity, surnames in chunk_identities.items():
        for surname in surnames:
            identities[identity].add(surname.lower())

# Show results by category
categories = {
    'Religious': ['jewish', 'sephardi', 'ashkenazi', 'court_jew', 'kohanim',
                 'quaker', 'huguenot', 'mennonite', 'puritan', 'calvinist', 
                 'presbyterian', 'catholic', 'protestant', 'muslim', 'sunni', 
                 'shia', 'parsee', 'hindu', 'maronite', 'coptic', 'greek_orthodox'],
    'Ethnic': ['armenian', 'greek', 'lebanese', 'syrian', 'palestinian', 
              'basque', 'hausa', 'yoruba', 'igbo', 'scottish', 'irish'],
    'Racial': ['black', 'african_american'],
    'Gender': ['female', 'woman', 'women', 'queen', 'princess', 'widow'],
    'Latino/Hispanic': ['latino', 'latina', 'hispanic', 'mexican', 'cuban', 
                       'puerto_rican', 'basque'],
}

for category, category_ids in categories.items():
    found = []
    for identity in sorted(identities.keys()):
        if identity in category_ids:
            families = sorted(list(identities[identity]))
            found.append((identity, len(families), families[:10]))
    
    if found:
        print(f"\n{category.upper()}:")
        print("-" * 70)
        for identity, count, examples in found:
            print(f"  {identity}: {count} families")
            if examples:
                print(f"    {', '.join(examples)}")

# Show uncategorized
all_categorized = [id for cat_list in categories.values() for id in cat_list]
uncategorized = sorted([id for id in identities.keys() if id not in all_categorized])

if uncategorized:
    print(f"\n\nOTHER:")
    print("-" * 70)
    for identity in uncategorized[:20]:  # Limit to first 20
        families = sorted(list(identities[identity]))
        print(f"  {identity}: {len(families)} families")
        print(f"    {', '.join(families[:10])}")

print()
print("="*70)
print(f"TOTAL: {len(identities)} different identities")
print(f"TOTAL: {sum(len(fams) for fams in identities.values())} family-identity detections")
print("="*70)

