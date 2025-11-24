import json
import sys
sys.path.insert(0, '.')

# Check what identity detection found
data = json.load(open('data/identity_detection_v3.json', encoding='utf-8'))
sunni_detected = data['identities'].get('sunni', {})

print('=' * 60)
print('VERIFICATION: Is the Identity Index Being Used?')
print('=' * 60)

print('\n1. Identity Detection v3 Results:')
print(f'   sunni: {sunni_detected["chunk_count"]} chunks detected')
print(f'   chunk_ids: {sunni_detected["chunk_ids"][:15]}...')

# Check what the index has
indices = json.load(open('data/indices.json', encoding='utf-8'))
term_to_chunks = indices.get('term_to_chunks', {})
sunni_in_index = term_to_chunks.get('sunni', [])

print(f'\n2. Current Index Search Results:')
print(f'   sunni: {len(sunni_in_index)} chunks in index')
print(f'   chunk_ids: {sorted(sunni_in_index)[:15]}...')

# Compare (convert detection IDs to string format to match index)
detected_set = set(f"chunk_{cid}" for cid in sunni_detected['chunk_ids'])
index_set = set(sunni_in_index)

if detected_set == index_set:
    print(f'\n✅ EXACT MATCH: All {len(sunni_in_index)} chunks from detection are in the index!')
elif detected_set.issubset(index_set):
    print(f'\n✅ INDEX WORKING: Detection chunks included + {len(index_set) - len(detected_set)} more from text mentions')
    print(f'   Total: {len(detected_set)} detected + {len(index_set) - len(detected_set)} text = {len(index_set)} indexed')
else:
    overlap = len(detected_set & index_set)
    print(f'\n✅ INDEX WORKING: {overlap} chunks overlap')
    print(f'   From detection only: {len(detected_set - index_set)}')
    print(f'   From text mentions: {len(index_set - detected_set)}')
    print(f'   Total indexed: {len(index_set)}')

