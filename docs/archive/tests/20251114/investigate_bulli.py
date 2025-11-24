import json
import chromadb

# Load index
with open('data/indices.json', encoding='utf-8') as f:
    idx = json.load(f)

# Get bullion chunks
bullion_chunks = idx['term_to_chunks'].get('bullion', [])
print(f"Bullion indexed in {len(bullion_chunks)} chunks:")
print(f"  Chunk IDs: {bullion_chunks[:5]}")
print()

# Load vector database to get actual text
client = chromadb.PersistentClient(path="data/vectordb")
collection = client.get_collection(name="historical_documents")

# Get first few bullion chunks
for chunk_id in bullion_chunks[:3]:
    results = collection.get(ids=[chunk_id], include=["documents", "metadatas"])
    if results and results['documents']:
        text = results['documents'][0]
        
        # Find "bulli" in the text
        text_lower = text.lower()
        if 'bulli' in text_lower:
            idx_pos = text_lower.find('bulli')
            # Show context around "bulli"
            start = max(0, idx_pos - 100)
            end = min(len(text), idx_pos + 150)
            
            print(f"Chunk {chunk_id}:")
            print(f"  ...{text[start:end]}...")
            print()

