"""Test if identity detector now finds actual Black bankers dynamically"""
import sys
sys.path.insert(0, '.')

from lib.identity_detector import detect_identities_from_index

print("Running improved identity detector...")
results, detector = detect_identities_from_index()

black_families = detector.identity_families.get('black', {})

print('\n' + '='*70)
print('BLACK BANKERS FOUND (DYNAMICALLY)')
print('='*70)

sorted_fams = sorted(black_families.items(), key=lambda x: x[1], reverse=True)
valid = [(f, c) for f, c in sorted_fams 
         if f not in detector.noise_words and len(f) > 3]

print(f'\nTotal: {len(valid)} families\n')

for fam, count in valid[:40]:
    print(f'  {fam.capitalize():<30} {count} mentions')

print('\n' + '='*70)
print('COMPARISON')
print('='*70)
print('Expected names: Brimmer, Rice, Jordan, Lewis, Raines, Ferguson, etc.')
print(f'Actually found: {len(valid)} families')
print('='*70)

