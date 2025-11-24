"""Verify regex detector finds all people user mentioned"""
import json
import sys
sys.path.insert(0, '.')

from lib.identity_detector import detect_identities_from_index

print("Running regex detector...")
results, detector = detect_identities_from_index(save_results=False)

# All people user mentioned
targets = {
    'LATINO/HISPANIC': ['alvarez', 'seix', 'goizueta', 'bañuelos', 'diaz', 'arboleya', 'chavez', 'salinas'],
    'BASQUE': ['bassoco', 'vial', 'echevarria', 'urquijo'],
    'LEBANESE (Lebanon)': ['sursock', 'chiha', 'solh', 'beidas', 'gemayel', 'sarkis', 'tamraz', 'khouri', 'faroun'],
    'LEBANESE (Wall St)': ['abdelnour', 'boutros', 'chammah', 'bitar', 'jabre', 'mack', 'noujaim'],
    'AFRICAN/NIGERIAN': ['dantata', 'okwei', 'maidawa', 'karda', 'musami', 'raccah', 'ogunlesi', 'thiam', 'ouattara'],
    'SAUDI/GULF': ['laden', 'rajhi'],
    'PALESTINIAN': ['beidas'],  # Already in Lebanese
}

print("\n" + "="*80)
print("VERIFICATION RESULTS")
print("="*80)

# Check each category
for category, names in targets.items():
    print(f"\n{category}:")
    
    # Find which identity detected these
    found_count = 0
    for name in names:
        found_in = []
        for identity, data in results['identities'].items():
            families = data.get('families', []) or data.get('individuals', [])
            if name in [f.lower() for f in families]:
                found_in.append(identity)
        
        if found_in:
            print(f"  [OK] {name:15} -> {', '.join(found_in)}")
            found_count += 1
        else:
            print(f"  [MISS] {name:15} -> NOT DETECTED")
    
    print(f"  Found: {found_count}/{len(names)}")

print("\n" + "="*80)

