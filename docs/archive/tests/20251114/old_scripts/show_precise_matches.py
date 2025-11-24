"""Show what the precise patterns are finding"""
import sys
sys.path.insert(0, '.')
from lib.cousinhood_detector import detect_cousinhoods_from_index

results, detector = detect_cousinhoods_from_index()

print("\n" + "="*80)
print("PRECISE PATTERN RESULTS")
print("="*80)

print("\n1. ALL FAMILIES FOUND (any count):")
print("-" * 80)

all_families = {}
for identity, families in detector.identity_families.items():
    for family, count in families.items():
        if family not in detector.noise_words and len(family) > 3:
            if family not in all_families:
                all_families[family] = {}
            all_families[family][identity] = count

# Sort by total count
family_totals = {f: sum(ids.values()) for f, ids in all_families.items()}
sorted_families = sorted(family_totals.items(), key=lambda x: x[1], reverse=True)

print(f"\nTop 40 families found:")
for family, total in sorted_families[:40]:
    identities = all_families[family]
    id_str = ', '.join([f"{id}:{cnt}" for id, cnt in sorted(identities.items(), key=lambda x: x[1], reverse=True)])
    print(f"  {family.capitalize():<20} (total:{total:3d})  {id_str}")

print("\n" + "="*80)
print("2. MULTI-IDENTITY FAMILIES (2+ different identities):")
print("-" * 80)

multi = {f: ids for f, ids in all_families.items() if len(ids) >= 2}
multi_sorted = sorted(multi.items(), key=lambda x: sum(x[1].values()), reverse=True)

for family, identities in multi_sorted[:20]:
    total = sum(identities.values())
    id_str = ', '.join([f"{id}:{cnt}" for id, cnt in sorted(identities.items(), key=lambda x: x[1], reverse=True)])
    print(f"  {family.capitalize():<20} (total:{total:3d})  {id_str}")

print("\n" + "="*80)
print("ANALYSIS")
print("="*80)
print(f"Total families found: {len(all_families)}")
print(f"Families with 2+ identities: {len(multi)}")
print(f"Families with 3+ identities: {len([f for f, ids in all_families.items() if len(ids) >= 3])}")
print(f"Families with 10+ mentions: {len([f for f, total in family_totals.items() if total >= 10])}")

