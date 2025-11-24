"""Test that Boston Brahmin (Protestant) and Hindu Brahmin are properly separated"""
import sys
sys.path.insert(0, '.')
from lib.cousinhood_detector import detect_cousinhoods_from_index

results, detector = detect_cousinhoods_from_index()

print("\n" + "="*80)
print("BRAHMIN DISAMBIGUATION TEST")
print("="*80)

print("\n1. BOSTON BRAHMIN (Protestant elite):")
print("-" * 80)
if 'boston_brahmin' in detector.identity_families:
    families = detector.identity_families['boston_brahmin']
    sorted_families = sorted(families.items(), key=lambda x: x[1], reverse=True)
    for family, count in sorted_families[:15]:
        if family not in detector.noise_words:
            print(f"  {family.capitalize():<20} {count} mentions")
else:
    print("  (none found)")

print("\n2. HINDU BRAHMIN (Hindu caste):")
print("-" * 80)
if 'hindu' in detector.identity_families:
    families = detector.identity_families['hindu']
    sorted_families = sorted(families.items(), key=lambda x: x[1], reverse=True)
    for family, count in sorted_families[:15]:
        if family not in detector.noise_words:
            print(f"  {family.capitalize():<20} {count} mentions")
else:
    print("  (none found)")

print("\n3. AMBIGUOUS BRAHMIN (should be empty or minimal after disambiguation):")
print("-" * 80)
if 'brahmin' in detector.identity_families:
    families = detector.identity_families['brahmin']
    sorted_families = sorted(families.items(), key=lambda x: x[1], reverse=True)
    if sorted_families:
        for family, count in sorted_families[:10]:
            if family not in detector.noise_words:
                print(f"  {family.capitalize():<20} {count} mentions")
    else:
        print("  (none - all successfully disambiguated!)")
else:
    print("  (none - all successfully disambiguated!)")

print("\n4. CHECK SPECIFIC FAMILIES:")
print("-" * 80)
test_families = ['lowell', 'cabot', 'adams', 'perkins', 'forbes', 'tagore']

for family in test_families:
    if family in detector.explicit_identities:
        identities = detector.explicit_identities[family]
        print(f"  {family.capitalize():<20} {', '.join(sorted(identities))}")
    else:
        print(f"  {family.capitalize():<20} (not found)")

print("\n" + "="*80)
print("RESULT:")
print("="*80)
boston_fams = set(detector.identity_families.get('boston_brahmin', {}).keys())
hindu_fams = set(detector.identity_families.get('hindu', {}).keys())
ambiguous_fams = set(detector.identity_families.get('brahmin', {}).keys())

# Remove noise
boston_fams = {f for f in boston_fams if f not in detector.noise_words}
hindu_fams = {f for f in hindu_fams if f not in detector.noise_words}
ambiguous_fams = {f for f in ambiguous_fams if f not in detector.noise_words}

print(f"Boston Brahmin families: {len(boston_fams)}")
print(f"Hindu families: {len(hindu_fams)}")
print(f"Ambiguous brahmin: {len(ambiguous_fams)}")
print(f"Overlap (Boston & generic): {len(boston_fams & ambiguous_fams)} (should be 0)")
print()
if len(boston_fams & ambiguous_fams) == 0:
    print("[SUCCESS] No overlap between Boston Brahmin and generic brahmin!")
else:
    print("[FAILURE] Some families tagged as both Boston Brahmin and generic brahmin")
    print(f"  Overlap: {boston_fams & ambiguous_fams}")

# Also check for Boston Brahmin / Hindu overlap
overlap_hindu = boston_fams & hindu_fams
print(f"Overlap (Boston & Hindu): {len(overlap_hindu)} (should be 0)")
if len(overlap_hindu) == 0:
    print("[SUCCESS] No overlap between Boston Brahmin (Protestant) and Hindu!")
else:
    print("[FAILURE] Some families tagged as both Boston Brahmin (Protestant) and Hindu")
    print(f"  Overlap: {overlap_hindu}")

