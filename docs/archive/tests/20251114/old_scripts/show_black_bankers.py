"""Show Black bankers found by identity detector"""
import sys
sys.path.insert(0, '.')

from lib.identity_detector import detect_identities_from_index

print("Running identity detector...")
results, detector = detect_identities_from_index()

black_families = detector.identity_families.get('black', {})

print('\n' + '='*70)
print('BLACK BANKERS FOUND BY IDENTITY DETECTOR')
print('='*70)

# Filter out noise words
sorted_fams = sorted(black_families.items(), key=lambda x: x[1], reverse=True)
valid = [(f, c) for f, c in sorted_fams 
         if f not in detector.noise_words and len(f) > 3 and c >= 2]

print(f'\nTotal: {len(valid)} families found\n')

if valid:
    for fam, count in valid[:50]:
        print(f'  {fam.capitalize():<30} {count} mentions')
else:
    print("  (None found with 2+ mentions)")

# Also check african_american
print('\n' + '='*70)
print('AFRICAN AMERICAN BANKERS')
print('='*70)

aa_families = detector.identity_families.get('african_american', {})
sorted_aa = sorted(aa_families.items(), key=lambda x: x[1], reverse=True)
valid_aa = [(f, c) for f, c in sorted_aa 
            if f not in detector.noise_words and len(f) > 3]

if valid_aa:
    for fam, count in valid_aa[:20]:
        print(f'  {fam.capitalize():<30} {count} mentions')
else:
    print("  (None found)")

print('\n' + '='*70)
print('NOTE: Detector may not be finding actual Black banker names.')
print('Let me search the documents directly for known Black bankers...')
print('='*70)

