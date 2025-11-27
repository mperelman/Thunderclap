"""
Post-Indexing Deduplication
===========================
Merges overlapping chunks after indexing to create unions of information.
Chunks that overlap are merged into single chunks containing all unique information.
"""

import os
import chromadb
from chromadb.config import Settings
from .config import DATA_DIR, COLLECTION_NAME, CHUNK_OVERLAP
from tqdm import tqdm
from collections import defaultdict
import re


def merge_overlapping_chunks(chunk1: str, chunk2: str, overlap_threshold: int = None) -> tuple:
    """
    Merge two overlapping chunks into a union.
    
    Args:
        chunk1: First chunk text
        chunk2: Second chunk text
        overlap_threshold: Minimum words to consider overlap (defaults to CHUNK_OVERLAP)
    
    Returns:
        Tuple of (merged_text, did_merge) where did_merge is True if chunks actually overlapped
    """
    overlap_threshold = overlap_threshold or CHUNK_OVERLAP
    
    words1 = chunk1.split()
    words2 = chunk2.split()
    
    # Case 1: End of chunk1 overlaps with start of chunk2
    if len(words1) >= overlap_threshold and len(words2) >= overlap_threshold:
        end_words1 = words1[-overlap_threshold:]
        start_words2 = words2[:overlap_threshold]
        
        if end_words1 == start_words2:
            # Merge: chunk1 + chunk2 (without duplicate overlap)
            return chunk1 + " " + " ".join(words2[overlap_threshold:])
    
    # Case 2: Start of chunk1 overlaps with end of chunk2
    if len(words1) >= overlap_threshold and len(words2) >= overlap_threshold:
        start_words1 = words1[:overlap_threshold]
        end_words2 = words2[-overlap_threshold:]
        
        if start_words1 == end_words2:
            # Merge: chunk2 + chunk1 (without duplicate overlap)
            return chunk2 + " " + " ".join(words1[overlap_threshold:])
    
    # Case 3: chunk2 is contained in chunk1
    if chunk2.lower() in chunk1.lower():
        return chunk1
    
    # Case 4: chunk1 is contained in chunk2
    if chunk1.lower() in chunk2.lower():
        return chunk2
    
    # Case 5: Partial overlap (more sophisticated)
    # Find longest common substring at boundaries
    # Check if last N words of chunk1 appear anywhere in chunk2
    for n in range(overlap_threshold, min(len(words1), len(words2)) + 1):
        if n > len(words1) or n > len(words2):
            break
        
        end_words1 = words1[-n:]
        # Check if these words appear at start of chunk2
        start_words2 = words2[:n]
        if end_words1 == start_words2:
            return chunk1 + " " + " ".join(words2[n:])
        
        # Check if these words appear anywhere in chunk2
        words2_str = " ".join(words2)
        end_words1_str = " ".join(end_words1)
        if end_words1_str in words2_str:
            # Find position and merge
            idx = words2_str.find(end_words1_str)
            if idx == 0:
                # At start, already handled above
                return chunk1 + " " + " ".join(words2[n:])
            else:
                # In middle or end - append non-overlapping part
                # This is trickier, so just concatenate
                return chunk1 + " " + chunk2
    
    # No overlap detected - return concatenated (shouldn't happen if called correctly)
    return chunk1 + " " + chunk2


def deduplicate_index():
    """
    Post-indexing deduplication: merge overlapping chunks in the database.
    
    Process:
    1. Load all chunks from ChromaDB
    2. Group chunks by document (only merge chunks from same document)
    3. Detect and merge overlapping chunks
    4. Update ChromaDB with merged chunks
    5. Update indices to point to merged chunk IDs
    """
    print("\n" + "="*80)
    print("POST-INDEXING DEDUPLICATION")
    print("="*80 + "\n")
    
    # Connect to database
    vectordb_path = os.path.join(DATA_DIR, 'vectordb')
    client = chromadb.PersistentClient(
        path=vectordb_path,
        settings=Settings(anonymized_telemetry=False)
    )
    
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except:
        print(f"[ERROR] Collection '{COLLECTION_NAME}' not found!")
        return
    
    # Get all chunks
    print("Step 1: Loading all chunks from database...")
    all_data = collection.get()
    all_chunks = all_data['documents']
    all_ids = all_data['ids']
    all_metadatas = all_data['metadatas']
    
    print(f"[OK] Loaded {len(all_chunks)} chunks\n")
    
    # Group chunks by document (filename)
    print("Step 2: Grouping chunks by document...")
    chunks_by_doc = defaultdict(list)
    for i, (chunk_id, chunk_text, metadata) in enumerate(zip(all_ids, all_chunks, all_metadatas)):
        filename = metadata.get('filename', 'unknown') if metadata else 'unknown'
        chunks_by_doc[filename].append((i, chunk_id, chunk_text, metadata))
    
    print(f"[OK] Grouped into {len(chunks_by_doc)} documents\n")
    
    # Process each document
    print("Step 3: Merging overlapping chunks within each document...")
    merged_chunks = []
    merged_ids = []
    merged_metadatas = []
    chunks_to_delete = set()
    id_mapping = {}  # old_id -> new_id (for index updates)
    
    total_merged = 0
    total_original = len(all_chunks)
    
    for filename, doc_chunks in tqdm(chunks_by_doc.items(), desc="Processing documents"):
        # Sort chunks by their original order (preserve document order)
        doc_chunks_sorted = sorted(doc_chunks, key=lambda x: x[0])
        
        # Process chunks sequentially, merging overlaps
        merged_doc_chunks = []
        used_indices = set()
        
        for i, (orig_idx, chunk_id, chunk_text, metadata) in enumerate(doc_chunks_sorted):
            if i in used_indices:
                continue
            
            # Try to merge with subsequent chunks
            merged_text = chunk_text
            merged_indices = {i}
            merged_id = chunk_id
            
            for j, (orig_idx2, chunk_id2, chunk_text2, metadata2) in enumerate(doc_chunks_sorted[i+1:], start=i+1):
                if j in used_indices:
                    continue
                
                # Check for overlap
                merged_result, did_merge = merge_overlapping_chunks(merged_text, chunk_text2)
                
                # If merge happened, mark as merged
                if did_merge:
                    # Overlap detected - merge
                    merged_text = merged_result
                    merged_indices.add(j)
                    used_indices.add(j)
                    chunks_to_delete.add(chunk_id2)
                    id_mapping[chunk_id2] = merged_id
                    total_merged += 1
            
            if len(merged_indices) > 1:
                # Multiple chunks merged
                print(f"    [MERGE] Merged {len(merged_indices)} chunks from {filename}")
            
            merged_doc_chunks.append((merged_id, merged_text, metadata))
            used_indices.add(i)
        
        # Add merged chunks to output
        for chunk_id, chunk_text, metadata in merged_doc_chunks:
            merged_chunks.append(chunk_text)
            merged_ids.append(chunk_id)
            merged_metadatas.append(metadata)
    
    print(f"\n[OK] Merged {total_merged} overlapping chunks")
    print(f"     Original: {total_original} chunks")
    print(f"     After merge: {len(merged_chunks)} chunks")
    print(f"     Reduction: {total_original - len(merged_chunks)} chunks ({100*(total_original-len(merged_chunks))/total_original:.1f}%)\n")
    
    # Step 4: Update ChromaDB
    print("Step 4: Updating database with merged chunks...")
    
    # Delete old collection
    client.delete_collection(COLLECTION_NAME)
    
    # Create new collection
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Add merged chunks in batches
    batch_size = 100
    for i in tqdm(range(0, len(merged_chunks), batch_size), desc="Adding merged chunks"):
        batch_chunks = merged_chunks[i:i+batch_size]
        batch_ids = merged_ids[i:i+batch_size]
        batch_metas = merged_metadatas[i:i+batch_size]
        
        collection.add(
            documents=batch_chunks,
            ids=batch_ids,
            metadatas=batch_metas
        )
    
    print(f"[OK] Database updated\n")
    
    # Step 5: Update indices
    print("Step 5: Updating indices to point to merged chunks...")
    import json
    indices_file = os.path.join(DATA_DIR, 'indices.json')
    
    if os.path.exists(indices_file):
        with open(indices_file, 'r') as f:
            indices = json.load(f)
        
        # Update term_to_chunks mapping
        updated_terms = 0
        for term, chunk_ids_list in indices.get('term_to_chunks', {}).items():
            updated_list = []
            for chunk_id in chunk_ids_list:
                # If chunk was merged, use new ID; otherwise keep original
                if chunk_id in id_mapping:
                    new_id = id_mapping[chunk_id]
                    if new_id not in updated_list:
                        updated_list.append(new_id)
                elif chunk_id not in chunks_to_delete:
                    updated_list.append(chunk_id)
            
            if updated_list != chunk_ids_list:
                indices['term_to_chunks'][term] = updated_list
                updated_terms += 1
        
        # Save updated indices
        with open(indices_file, 'w') as f:
            json.dump(indices, f, indent=2)
        
        print(f"[OK] Updated {updated_terms} term mappings\n")
    else:
        print(f"[WARNING] Indices file not found: {indices_file}\n")
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Original chunks: {total_original:,}")
    print(f"Merged chunks: {total_merged:,}")
    print(f"Final chunks: {len(merged_chunks):,}")
    print(f"Reduction: {total_original - len(merged_chunks):,} chunks ({100*(total_original-len(merged_chunks))/total_original:.1f}%)")
    print(f"\n[SUCCESS] Deduplication complete!")
    print(f"Location: {DATA_DIR}")


if __name__ == "__main__":
    import os
    deduplicate_index()

