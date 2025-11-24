import json

# Load chunks
with open('data/chunks.json', encoding='utf-8') as f:
    chunks = json.load(f)

# Find Bulli as a name (not bullion)
bulli_chunks = []
for chunk in chunks:
    text_lower = chunk['text'].lower()
    if 'bulli' in text_lower:
        # Check if it's the name Bulli, not just part of bullion
        if ' bulli ' in text_lower or text_lower.startswith('bulli ') or text_lower.endswith(' bulli'):
            bulli_chunks.append(chunk)

print(f"Chunks with 'Bulli' as a name (not bullion): {len(bulli_chunks)}")
print()

if bulli_chunks:
    for chunk in bulli_chunks[:3]:
        print(f"Chunk {chunk['id']}:")
        print(f"  {chunk['text'][:300]}...")
        print()
else:
    print("No chunks found with 'Bulli' as a standalone name.")
    print()
    print("Checking bullion chunks to see if Bulli is mentioned:")
    
    # Load index to get bullion chunks
    with open('data/indices.json', encoding='utf-8') as f:
        idx = json.load(f)
    
    bullion_chunk_ids = idx['term_to_chunks'].get('bullion', [])
    print(f"  Bullion has {len(bullion_chunk_ids)} chunks")
    
    # Check first few bullion chunks
    for cid in bullion_chunk_ids[:3]:
        chunk = next((c for c in chunks if c['id'] == cid), None)
        if chunk:
            text = chunk['text']
            # Find context around 'bulli'
            idx_pos = text.lower().find('bulli')
            if idx_pos != -1:
                start = max(0, idx_pos - 50)
                end = min(len(text), idx_pos + 100)
                print(f"\n  {cid}: ...{text[start:end]}...")



