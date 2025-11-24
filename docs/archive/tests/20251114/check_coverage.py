import json

indices = json.load(open('data/indices.json', encoding='utf-8'))
jewish_chunks = indices['term_to_chunks'].get('jewish', [])

print('=' * 60)
print('COVERAGE ANALYSIS: "jewish bankers"')
print('=' * 60)

print('\nIdentity Detection + Text Mentions:')
print(f'  Total "jewish" chunks in index: {len(jewish_chunks)}')

print('\nYour Query Used:')
print('  Keyword search found: 143 chunks')
print('  Combined with semantic: 50 chunks (CAPPED)')

print(f'\nCoverage Rate: 50 / {len(jewish_chunks)} = {50/len(jewish_chunks)*100:.1f}%')

print('\n' + '=' * 60)
print('WHY THE NARRATIVE IS DISJOINTED')
print('=' * 60)

print(f'''
❌ Problem: Using only 50 chunks from {len(jewish_chunks)} available

This causes:
1. DISJOINTED
   - Sampling creates gaps in continuity
   - No narrative flow between disconnected chunks
   
2. JUMPS AROUND
   - 50 chunks randomly distributed across 8+ centuries
   - No systematic coverage of any time period
   
3. UNEVEN COVERAGE
   - Semantic search clusters where terms co-occur
   - Heavy in 18th century (French Revolution, Rothschild)
   - Light everywhere else (Middle Ages, 19th-20th century)

Solution: Need more chunks or better time-period distribution
''')

