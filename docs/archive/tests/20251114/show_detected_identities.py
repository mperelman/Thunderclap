"""Show what identities were detected in the documents"""
import json
from pathlib import Path

# Load detected identities
detected_file = Path('data/detected_identities.json')
if detected_file.exists():
    with open(detected_file) as f:
        data = json.load(f)
    
    identities = data.get('identities', {})
    
    print("="*70)
    print("DETECTED IDENTITIES IN YOUR DOCUMENTS")
    print("="*70)
    print()
    
    # Group by category
    categories = {
        'Religious': ['jewish', 'sephardi', 'ashkenazi', 'court_jew', 'kohanim',
                     'quaker', 'huguenot', 'mennonite', 'puritan', 'calvinist', 
                     'presbyterian', 'catholic_irish', 'catholic', 'protestant',
                     'muslim', 'sunni', 'shia', 'alawite', 'druze', 'maronite',
                     'coptic', 'greek_orthodox', 'parsee', 'zoroastrian', 'hindu'],
        'Ethnic': ['armenian', 'greek', 'lebanese', 'syrian', 'palestinian', 
                  'basque', 'hausa', 'yoruba', 'igbo', 'fulani', 'akan', 'zulu',
                  'scottish', 'irish', 'welsh', 'german', 'french'],
        'Racial': ['black', 'white'],
        'Gender': ['female', 'male', 'woman', 'women', 'queen', 'princess', 'lady', 'widow'],
        'Geographic': ['american', 'british', 'french', 'german', 'russian', 
                      'lebanese', 'nigerian', 'mexican', 'cuban'],
        'Other': []
    }
    
    for category, category_identities in categories.items():
        found_in_category = []
        
        for identity in sorted(identities.keys()):
            if identity in category_identities:
                families = identities[identity]
                found_in_category.append((identity, len(families), list(families.keys())[:5]))
        
        if found_in_category:
            print(f"{category.upper()}:")
            print("-" * 70)
            for identity, count, examples in found_in_category:
                print(f"  {identity}: {count} families")
                if examples:
                    print(f"    Examples: {', '.join(examples)}")
            print()
    
    # Show any identities not in predefined categories
    all_categorized = [id for cat_list in categories.values() for id in cat_list]
    uncategorized = [id for id in identities.keys() if id not in all_categorized]
    
    if uncategorized:
        print("OTHER DETECTED:")
        print("-" * 70)
        for identity in sorted(uncategorized):
            families = identities[identity]
            print(f"  {identity}: {len(families)} families")
            examples = list(families.keys())[:5]
            if examples:
                print(f"    Examples: {', '.join(examples)}")
        print()
    
    print("="*70)
    print(f"TOTAL: {len(identities)} different identity types detected")
    print(f"TOTAL: {sum(len(fams) for fams in identities.values())} family-identity associations")
    print("="*70)

else:
    print("[ERROR] No detected_identities.json found")
    print("Run: python lib/llm_identity_detector.py")


