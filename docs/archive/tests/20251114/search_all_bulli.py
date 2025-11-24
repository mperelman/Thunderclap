import chromadb

# Connect to database
client = chromadb.PersistentClient(path="data/vectordb")
collection = client.get_collection(name="historical_documents")

# Get ALL documents
all_docs = collection.get(include=["documents", "metadatas"])

print(f"Searching {len(all_docs['documents'])} chunks for 'Bulli' (family name)...")
print()

found = []
for i, text in enumerate(all_docs['documents']):
    text_lower = text.lower()
    
    # Look for "Bulli" as a name (not just part of bullion)
    # Check for word boundaries or common name patterns
    if (' bulli ' in text_lower or ' bulli,' in text_lower or 
        ' bulli.' in text_lower or ' bulli)' in text_lower or 
        ' bulli\'s' in text_lower or text_lower.startswith('bulli ') or 
        text_lower.endswith(' bulli')):
        chunk_id = all_docs['ids'][i]
        # Find context
        idx_pos = text_lower.find('bulli')
        start = max(0, idx_pos - 80)
        end = min(len(text), idx_pos + 120)
        
        found.append({
            'id': chunk_id,
            'context': text[start:end]
        })

if found:
    print(f"Found {len(found)} chunks with 'Bulli' as a name:\n")
    for item in found[:10]:
        print(f"Chunk {item['id']}:")
        print(f"  ...{item['context']}...")
        print()
else:
    print("No chunks found with 'Bulli' as a standalone name.")
    print()
    print("Checking if 'Bulli' appears as part of a longer name...")
    
    # Check for any occurrence at all
    any_bulli = [i for i, text in enumerate(all_docs['documents']) if 'bulli' in text.lower()]
    print(f"  Chunks containing 'bulli' (any form): {len(any_bulli)}")
    
    if any_bulli:
        print(f"\n  First occurrence (chunk {all_docs['ids'][any_bulli[0]]}):")
        text = all_docs['documents'][any_bulli[0]]
        idx_pos = text.lower().find('bulli')
        start = max(0, idx_pos - 80)
        end = min(len(text), idx_pos + 120)
        print(f"    ...{text[start:end]}...")

