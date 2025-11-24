import json

indices = json.load(open('data/indices.json', encoding='utf-8'))

ob_chunks = set(indices['term_to_chunks'].get('old_believer', []))
ob_chunks_alt = set(indices['term_to_chunks'].get('old', []))
jewish_chunks = set(indices['term_to_chunks'].get('jewish', []))
bukharan_chunks = set(indices['term_to_chunks'].get('bukharan', []))

print(f'Old Believer chunks: {len(ob_chunks)}')
print(f'Jewish chunks: {len(jewish_chunks)}')
print(f'Bukharan chunks: {len(bukharan_chunks)}')
print()
print('Overlap analysis:')
print(f'  OldBeliever ∩ Jewish: {len(ob_chunks & jewish_chunks)}')
print(f'  OldBeliever ∩ Bukharan: {len(ob_chunks & bukharan_chunks)}')
print()

if len(ob_chunks & (jewish_chunks | bukharan_chunks)) == 0:
    print('❌ PROBLEM: Old Believer chunks do not overlap with Jewish/Bukharan')
    print('   The comparison chunk mentions Old Believers as counterparts to Jews')
    print('   But it is tagged jewish/bukharan, not old_believer')
    print('   So Old Believer query misses the comparison!')
else:
    print('✅ Some overlap exists - comparison should appear in narrative')




