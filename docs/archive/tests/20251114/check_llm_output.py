"""Check what LLM actually returned"""
import json

cache = json.load(open('data/llm_identity_cache.json', encoding='utf-8'))

v2_chunks = [(h, d) for h, d in cache.items() 
             if d.get('prompt_version') == 'v2' and d.get('identities')]

print(f"v2 chunks with identities: {len(v2_chunks)}\n")

if v2_chunks:
    print("First 3 detections:")
    print("=" * 70)
    
    for i, (chunk_hash, data) in enumerate(v2_chunks[:3], 1):
        print(f"\n{i}. Chunk: {chunk_hash[:12]}...")
        print(f"   Preview: {data.get('text_preview', '')[:80]}")
        print(f"   Identities: {data.get('identities', {})}")
else:
    print("No v2 chunks with identities found")


