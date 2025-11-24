"""
Build Index with Endnotes
==========================
Builds the complete index including:
1. Body text chunks (searchable)
2. Endnotes (stored for retrieval)
3. Chunk-to-endnote mappings
"""

import sys
import os
sys.path.insert(0, '.')

from lib.document_parser import load_all_documents
from lib.index_builder import build_indices, build_endnote_mappings, save_indices, split_into_chunks, augment_indices_with_identities, create_deduplicated_term_files
from lib.config import DATA_DIR, COLLECTION_NAME
import chromadb
from chromadb.config import Settings
import json

def build_complete_index():
    """Build complete index with body chunks and endnotes."""
    
    print("\n" + "="*80)
    print("BUILDING INDEX WITH ENDNOTES")
    print("="*80 + "\n")
    
    # Step 1: Load documents (with endnotes)
    print("Step 1: Loading documents...")
    documents = load_all_documents(use_cache=False)  # Force re-parse to get endnotes
    print(f"[OK] Loaded {len(documents)} documents\n")
    
    # Step 2: Chunk body text
    print("Step 2: Chunking body text...")
    all_chunks = []
    chunk_ids = []
    chunk_metadatas = []
    chunk_counter = 0
    
    for doc in documents:
        text = doc['text']  # Combined body text
        filename = doc['filename']
        chunks = split_into_chunks(text)
        
        for chunk in chunks:
            all_chunks.append(chunk)
            chunk_ids.append(f"chunk_{chunk_counter}")
            chunk_metadatas.append({'filename': filename, 'type': 'body'})
            chunk_counter += 1
    
    print(f"[OK] Created {len(all_chunks)} body chunks\n")
    
    # Step 3: Build term indices (for body chunks)
    print("Step 3: Building term indices...")
    indices = build_indices(all_chunks, chunk_ids)
    print()
    
    # Step 3b: Load identity detection results and augment indices
    print("Step 3b: Loading identity detection results...")
    try:
        identity_file = os.path.join(DATA_DIR, 'identity_detection_v3.json')
        if os.path.exists(identity_file):
            with open(identity_file, 'r', encoding='utf-8') as f:
                identity_data = json.load(f)
            
            print(f"  [OK] Loaded {len(identity_data['identities'])} identities from v3 detection\n")
            
            # Augment indices with identity metadata
            print("Step 3c: Augmenting indices with identity metadata...")
            augmentation_count = 0
            
            # Import TERM_GROUPS to find all variants for each identity
            from lib.index_builder import TERM_GROUPS
            
            for identity, data in identity_data['identities'].items():
                identity_lower = identity.lower()
                chunk_ids_from_detection = data['chunk_ids']
                
                # Convert integer chunk IDs to string chunk IDs (e.g., 123 -> "chunk_123")
                chunk_ids_str = [f"chunk_{cid}" for cid in chunk_ids_from_detection]
                
                # Find all variants for this identity in TERM_GROUPS
                # This ensures "black" and "blacks" both get updated
                variants_to_update = [identity_lower]  # Start with the identity itself
                for main_term, variants in TERM_GROUPS.items():
                    if identity_lower in variants or identity_lower == main_term:
                        # Add all variants in this group
                        variants_to_update.extend(variants)
                        variants_to_update.append(main_term)
                
                # Deduplicate variants
                variants_to_update = list(set(variants_to_update))
                
                # Add chunks to ALL variants to preserve TERM_GROUPS merges
                for variant in variants_to_update:
                    if variant in indices['term_to_chunks']:
                        existing = set(indices['term_to_chunks'][variant])
                        for chunk_id in chunk_ids_str:
                            if chunk_id not in existing:
                                indices['term_to_chunks'][variant].append(chunk_id)
                                existing.add(chunk_id)
                                augmentation_count += 1
                    else:
                        indices['term_to_chunks'][variant] = chunk_ids_str.copy()
                        augmentation_count += len(chunk_ids_str)
            
            print(f"  [OK] Augmented {len(identity_data['identities'])} identities")
            print(f"  [OK] Added {augmentation_count} new chunk mappings\n")
        else:
            print(f"  [WARNING] No identity detection file found at {identity_file}")
            print(f"  [SKIP] Continuing without identity augmentation\n")
    except Exception as e:
        print(f"  [WARNING] Identity augmentation failed: {e}")
        import traceback
        traceback.print_exc()
        print(f"  [SKIP] Continuing without identity augmentation\n")
    
    # Save indices (now with identity augmentation)
    save_indices(indices)
    
    # Step 4: Build endnote mappings
    print("Step 4: Building endnote mappings...")
    endnote_data = build_endnote_mappings(documents, all_chunks, chunk_ids)
    print()
    
    # Step 5: Build vector database (for body chunks)
    print("Step 5: Building vector database...")
    vectordb_path = os.path.join(DATA_DIR, 'vectordb')
    
    client = chromadb.PersistentClient(
        path=vectordb_path,
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Delete existing collection
    try:
        client.delete_collection(COLLECTION_NAME)
    except:
        pass
    
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Add in batches
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[i:i+batch_size]
        batch_ids = chunk_ids[i:i+batch_size]
        batch_metas = chunk_metadatas[i:i+batch_size]
        
        collection.add(
            documents=batch_chunks,
            ids=batch_ids,
            metadatas=batch_metas
        )
        print(f"  Added {len(batch_ids)} chunks ({i+len(batch_ids)}/{len(all_chunks)})")
    
    print(f"[OK] Vector database built\n")
    
    # Step 6: Create deduplicated text files per indexed term
    # NOTE: This runs AFTER TERM_GROUPS has merged chunk IDs in Step 3.
    #       Deduplication processes the already-merged chunks to remove duplicate text.
    print("Step 6: Creating deduplicated text files per indexed term...")
    files_created = create_deduplicated_term_files(indices, all_chunks, chunk_ids, min_chunks=25)
    print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Body chunks indexed: {len(all_chunks):,}")
    print(f"Endnotes collected: {len(endnote_data['all_endnotes']):,}")
    print(f"Chunks with endnotes: {len(endnote_data['chunk_to_endnotes']):,}")
    print(f"Terms indexed: {len(indices['term_to_chunks']):,}")
    print(f"Deduplicated term files: {files_created:,}")
    print(f"\n[SUCCESS] Index built successfully!")
    print(f"Location: {DATA_DIR}")

if __name__ == "__main__":
    build_complete_index()


