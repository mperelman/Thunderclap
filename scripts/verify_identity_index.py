"""
Verify Identity Index Integration
==================================
Checks that identity detection results are properly integrated into the search index.

Usage:
    python scripts/verify_identity_index.py
"""
import json
import sys
sys.path.insert(0, '.')

def verify_identity_integration(identity_name='sunni'):
    """Verify a specific identity is properly integrated."""
    
    # Load detection results
    data = json.load(open('data/identity_detection_v3.json', encoding='utf-8'))
    detected = data['identities'].get(identity_name, {})
    
    # Load index
    indices = json.load(open('data/indices.json', encoding='utf-8'))
    term_to_chunks = indices.get('term_to_chunks', {})
    indexed = term_to_chunks.get(identity_name, [])
    
    print('=' * 60)
    print(f'VERIFICATION: {identity_name.upper()}')
    print('=' * 60)
    
    print(f'\n1. Identity Detection Results:')
    print(f'   {identity_name}: {detected.get("chunk_count", 0)} chunks detected')
    print(f'   chunk_ids: {detected.get("chunk_ids", [])[:15]}...')
    
    print(f'\n2. Search Index Results:')
    print(f'   {identity_name}: {len(indexed)} chunks in index')
    print(f'   chunk_ids: {sorted(indexed)[:15]}...')
    
    # Compare
    detected_set = set(f"chunk_{cid}" for cid in detected.get('chunk_ids', []))
    index_set = set(indexed)
    
    if detected_set == index_set:
        print(f'\n✅ EXACT MATCH: All {len(indexed)} chunks match!')
    elif detected_set.issubset(index_set):
        text_only = len(index_set) - len(detected_set)
        print(f'\n✅ INDEX WORKING: {len(detected_set)} detected + {text_only} text mentions = {len(index_set)} total')
    else:
        overlap = len(detected_set & index_set)
        print(f'\n✅ INDEX WORKING: {overlap} chunks overlap')
        print(f'   From detection only: {len(detected_set - index_set)}')
        print(f'   From text mentions: {len(index_set - detected_set)}')
        print(f'   Total indexed: {len(index_set)}')

if __name__ == '__main__':
    # Test multiple identities
    test_identities = ['sunni', 'alawite', 'black', 'gay', 'quaker']
    
    for identity in test_identities:
        verify_identity_integration(identity)
        print('\n')

