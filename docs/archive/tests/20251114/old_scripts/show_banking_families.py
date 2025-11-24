"""Show banking families with multiple attributes"""
import sys
sys.path.insert(0, '.')

from lib.cousinhood_detector import detect_cousinhoods_from_index

# Known banking families to check
known_families = [
    'warburg', 'rothschild', 'sassoon', 'oppenheim', 'barclay', 'lloyd', 
    'hope', 'mallet', 'teixeira', 'hambro', 'morgan', 'cabot', 'lowell',
    'tata', 'wadia', 'mendes', 'lazard', 'kuhn', 'seligman', 'delbanco',
    'schroder', 'baring', 'smyth', 'bevan', 'stein', 'schaaffhausen',
    'dietrich', 'clercq', 'boissevain', 'neufville', 'perkins', 'forbes',
    'balian', 'dadian', 'gulbenkian', 'tagore', 'adani', 'ambani',
    'samsung', 'hyundai', 'sophonpanich', 'lamsam', 'salim', 'riady'
]

print("Loading detected cousinhoods...")
results, detector = detect_cousinhoods_from_index()

print("\n" + "="*80)
print("BANKING FAMILIES WITH MULTIPLE ATTRIBUTES")
print("="*80)

found_count = 0
for family in known_families:
    if family in detector.explicit_identities:
        attrs = detector.explicit_identities[family]
        if len(attrs) > 1:
            print(f"{family.capitalize():<20} = {', '.join(sorted(attrs))}")
            found_count += 1
        elif len(attrs) == 1:
            print(f"{family.capitalize():<20} = {list(attrs)[0]} (single attribute)")

print(f"\n{found_count} banking families have multiple attributes!")

print("\n" + "="*80)
print("IDENTITY COUNTS PER FAMILY")
print("="*80)

for family in ['warburg', 'rothschild', 'sassoon', 'teixeira', 'oppenheim', 'hambro', 'barclay']:
    if family in detector.identity_families.get('jewish', {}):
        jewish_count = detector.identity_families['jewish'][family]
    else:
        jewish_count = 0
    
    if family in detector.identity_families.get('sephardim', {}):
        seph_count = detector.identity_families['sephardim'][family]
    else:
        seph_count = 0
    
    if family in detector.identity_families.get('court_jew', {}):
        court_count = detector.identity_families['court_jew'][family]
    else:
        court_count = 0
        
    if family in detector.identity_families.get('quaker', {}):
        quaker_count = detector.identity_families['quaker'][family]
    else:
        quaker_count = 0
    
    if family in detector.identity_families.get('mennonite', {}):
        mennonite_count = detector.identity_families['mennonite'][family]
    else:
        mennonite_count = 0
    
    print(f"{family.capitalize():<15} Jewish:{jewish_count:>3}  Sephardi:{seph_count:>2}  Court:{court_count:>2}  Quaker:{quaker_count:>2}  Mennonite:{mennonite_count:>2}")

print("\n" + "="*80)
print("ANCESTRY RELATIONSHIPS")
print("="*80)

if detector.family_ancestry:
    for family, ancestry in sorted(detector.family_ancestry.items()):
        origin_fam = ancestry.get('origin_family', '')
        origin_id = ancestry.get('origin_identity', '')
        if origin_fam:
            print(f"  {family.capitalize():<15} descended from {origin_id.capitalize()} {origin_fam.capitalize()}")
else:
    print("  No explicit ancestry statements detected with current patterns")

