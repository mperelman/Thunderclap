import sys
sys.path.insert(0, '.')

from lib.query_engine import QueryEngine
import chromadb

# Initialize query engine
qe = QueryEngine()

# Search for Hohenemser  
results = qe.search_term('hohenemser', max_results=10)

print(f"Found {len(results)} chunks about Hohenemser:\n")
print("="*80)

# Load database to get full text
client = chromadb.PersistentClient(path='data/vectordb')
collection = client.get_collection(name='historical_documents')

for i, result in enumerate(results[:4], 1):
    # Result might be tuple of (chunk_text, metadata) or dict
    if isinstance(result, tuple):
        text, metadata = result
        chunk_id = metadata.get('chunk_id', f'unknown_{i}')
    elif isinstance(result, dict):
        chunk_id = result.get('chunk_id', result.get('id', f'unknown_{i}'))
        text = result.get('text', result.get('document', ''))
    else:
        print(f"Unknown result type: {type(result)}")
        continue
    
    print(f"\n{i}. Chunk {chunk_id}:")
    print("-" * 80)
    print(text[:500] + "..." if len(text) > 500 else text)
    print()

