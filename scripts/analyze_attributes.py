"""Quick script to analyze multi-attribute families"""
import sys
sys.path.insert(0, '.')

from lib.identity_detector import detect_identities_from_index

print("Running identity/attribute detector...")
results, detector = detect_identities_from_index(save_results=True)

print("\n" + "="*80)
print("FAMILIES WITH MULTIPLE ATTRIBUTES (Top 30)")
print("="*80)

# Find families with multiple identities
multi = {
    f: ids 
    for f, ids in detector.explicit_identities.items() 
    if len(ids) > 1 and f not in detector.noise_words and len(f) > 3
}

count = 0
for family, attrs in sorted(multi.items()):
    if count >= 30:
        break
    attrs_list = sorted(attrs)
    print(f"{family.capitalize():<20} = {', '.join(attrs_list)}")
    count += 1

print("\n" + "="*80)
print("EXPLICIT ANCESTRY (Descended From)")
print("="*80)

for family, ancestry in sorted(detector.family_ancestry.items())[:20]:
    origin_fam = ancestry.get('origin_family', '')
    origin_id = ancestry.get('origin_identity', '')
    if origin_fam:
        print(f"  {family.capitalize():<15} descended from {origin_id.capitalize()} {origin_fam.capitalize()}")

print("\n" + "="*80)
print("KEY FINDINGS")
print("="*80)
print(f"Total families identified: {len(detector.explicit_identities)}")
print(f"Families with multiple attributes: {len(multi)}")
print(f"Explicit ancestry statements: {len(detector.family_ancestry)}")

