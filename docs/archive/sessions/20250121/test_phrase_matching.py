import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.query_engine import QueryEngine

engine = QueryEngine()

# Test different queries
queries = [
    "Rothschild Paris",
    "tell me about Rothschild Paris",
    "Rothschild London",
    "Lazard Paris",
    "Rothschild Vienna"
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: '{query}'")
    print('='*60)
    
    # Extract keywords manually to see what's happening
    raw_tokens = query.lower().split()
    from lib.query_engine import SUBJECT_GENERIC_TERMS
    keywords = [t for t in raw_tokens if t not in ['tell', 'me', 'about', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'from', 'by']]
    meaningful = [k for k in keywords if k not in SUBJECT_GENERIC_TERMS]
    
    print(f"Keywords: {keywords}")
    print(f"Meaningful: {meaningful}")
    
    if len(meaningful) >= 2:
        for i in range(len(meaningful) - 1):
            phrase = f"{meaningful[i]} {meaningful[i+1]}"
            print(f"  Checking phrase: '{phrase}'")
            if phrase in engine.term_to_chunks:
                print(f"    FOUND in index: {len(engine.term_to_chunks[phrase])} chunks")
            else:
                print(f"    NOT in index")
    
    # Now test actual query
    result = engine.query(query, use_llm=False)
    print(f"Result: Found {len(result.split('Found')[1].split('relevant')[0].strip()) if 'Found' in result else 'N/A'} chunks")

