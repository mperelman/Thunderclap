"""Test if query API actually works"""
import sys
sys.path.insert(0, '.')

from query import ask

print("Testing query with LLM...")
try:
    result = ask('panic of 1925', use_llm=True)
    print(f'[SUCCESS] Generated {len(result)} characters')
    
    with open('temp/panic_1925_narrative.txt', 'w', encoding='utf-8') as f:
        f.write(result)
    
    print('[SAVED] temp/panic_1925_narrative.txt')
    print('\nThis means at least one API key has quota!')
    print('The detector should work too!')
    
except Exception as e:
    print(f'[FAIL] {e}')
    print('API quota exhausted')

