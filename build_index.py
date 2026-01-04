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
from lib.panic_indexer import augment_index_with_panics
from lib.config import DATA_DIR, COLLECTION_NAME
import chromadb
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
    
    # Step 3a: Augment indices with panic terms
    print("Step 3a: Augmenting indices with panic terms...")
    indices['term_to_chunks'] = augment_index_with_panics(indices['term_to_chunks'], all_chunks, chunk_ids)
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
                
                # CRITICAL: Also add space/underscore versions for multi-word identities
                # Identity detector uses underscores (e.g., "court_jew") but TERM_GROUPS uses spaces
                # Add both versions to ensure merging
                if '_' in identity_lower:
                    space_version = identity_lower.replace('_', ' ')
                    variants_to_update.append(space_version)
                elif ' ' in identity_lower:
                    underscore_version = identity_lower.replace(' ', '_')
                    variants_to_update.append(underscore_version)
                
                # Deduplicate variants
                variants_to_update = list(set(variants_to_update))
                
                # Add chunks to ALL variants to preserve TERM_GROUPS merges
                # CRITICAL: Skip generic terms that should not be in the index
                from lib.constants import GENERIC_WORDS_TO_EXCLUDE, GENERIC_PHRASES_TO_EXCLUDE
                def should_exclude_term(term):
                    """Check if term should be excluded (word or phrase)."""
                    term_lower = term.lower()
                    if term_lower in GENERIC_WORDS_TO_EXCLUDE:
                        return True
                    if term_lower in GENERIC_PHRASES_TO_EXCLUDE:
                        return True
                    return False
                
                for variant in variants_to_update:
                    # CRITICAL: Skip generic terms - they should not be in the index
                    if should_exclude_term(variant):
                        continue
                    
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
            
            # CRITICAL: After identity augmentation, re-merge TERM_GROUPS to include underscore versions
            # Identity detector creates underscore versions (e.g., "court_jew") AFTER TERM_GROUPS merging
            # So we need to merge them again now that identity augmentation has added them
            print("  Re-merging TERM_GROUPS to include identity-augmented underscore versions...")
            for main_term, variants in TERM_GROUPS.items():
                merged_chunk_set = set()  # Use different variable name to avoid shadowing outer all_chunks
                # Collect from all space variants
                for variant in variants:
                    if variant in indices['term_to_chunks']:
                        merged_chunk_set.update(indices['term_to_chunks'][variant])
                # Collect from underscore versions
                main_term_underscore = main_term.replace(' ', '_')
                if main_term_underscore in indices['term_to_chunks']:
                    merged_chunk_set.update(indices['term_to_chunks'][main_term_underscore])
                for variant in variants:
                    variant_underscore = variant.replace(' ', '_')
                    if variant_underscore in indices['term_to_chunks']:
                        merged_chunk_set.update(indices['term_to_chunks'][variant_underscore])
                
                if merged_chunk_set:
                    merged_list = list(merged_chunk_set)
                    indices['term_to_chunks'][main_term] = merged_list
                    for variant in variants:
                        indices['term_to_chunks'][variant] = merged_list.copy()
                    indices['term_to_chunks'][main_term_underscore] = merged_list.copy()
            
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
    
    # Step 3d: Final filter - remove generic terms that may have been added by identity augmentation
    # CRITICAL: This runs AFTER identity augmentation to ensure generic terms are never in the index
    # Hyperlinking is based on what's in the index, so we must remove generic terms here
    print("Step 3d: Final filtering (removing generic terms)...")
    from lib.constants import GENERIC_WORDS_TO_EXCLUDE, GENERIC_PHRASES_TO_EXCLUDE
    def should_exclude_term(term):
        """Check if term should be excluded (word or phrase)."""
        term_lower = term.lower()
        if term_lower in GENERIC_WORDS_TO_EXCLUDE:
            return True
        if term_lower in GENERIC_PHRASES_TO_EXCLUDE:
            return True
        return False
    
    # Remove generic terms from index
    terms_before = len(indices['term_to_chunks'])
    indices['term_to_chunks'] = {t: chunks for t, chunks in indices['term_to_chunks'].items() if not should_exclude_term(t)}
    terms_after = len(indices['term_to_chunks'])
    removed = terms_before - terms_after
    print(f"  [OK] Removed {removed} generic terms (final filter)")
    print(f"  [INFO] Index contains {terms_after:,} terms (filtered)\n")
    
    # Save indices (now with identity augmentation)
    save_indices(indices)
    
    # Step 4: Build endnote mappings
    print("Step 4: Building endnote mappings...")
    endnote_data = build_endnote_mappings(documents, all_chunks, chunk_ids)
    print()
    
    # Step 5: Build vector database (for body chunks)
    print("Step 5: Building vector database...")
    vectordb_path = os.path.join(DATA_DIR, 'vectordb')
    
    # Check write permissions first
    print(f"  [INFO] Checking write permissions for {DATA_DIR}...")
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        test_file = os.path.join(DATA_DIR, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print(f"  [OK] Write permissions confirmed for {DATA_DIR}")
    except Exception as e:
        print(f"  [ERROR] Cannot write to {DATA_DIR}: {e}")
        print(f"  [ERROR] Volume may be read-only or permissions issue")
        raise Exception(f"Cannot write to data directory: {e}")
    
    # CRITICAL: Delete entire vectordb directory to avoid "different settings" error
    # This happens when ChromaDB was initialized elsewhere (e.g., by QueryEngine during startup)
    if os.path.exists(vectordb_path):
        print(f"  [INFO] Removing existing vectordb directory to avoid settings conflict...")
        import shutil
        import gc
        try:
            # Force garbage collection to close any open ChromaDB file handles
            # This is critical - SQLite files can be locked by open connections
            gc.collect()
            import time
            time.sleep(2)  # Wait for file handles to close
            
            # Try to remove SQLite file first (it might be locked)
            sqlite_file = os.path.join(vectordb_path, 'chroma.sqlite3')
            if os.path.exists(sqlite_file):
                try:
                    os.remove(sqlite_file)
                    print(f"  [INFO] Removed SQLite database file")
                    time.sleep(1)  # Brief pause after removing SQLite file
                except Exception as e:
                    print(f"  [WARN] Could not remove SQLite file (may be locked): {e}")
                    # Continue anyway - might still be able to remove directory
            
            # Now remove the entire directory
            shutil.rmtree(vectordb_path)
            print(f"  [OK] Removed existing vectordb directory")
            
            # Wait before recreating
            time.sleep(1)
            
            # Recreate directory with explicit permissions
            os.makedirs(vectordb_path, mode=0o755, exist_ok=True)
            print(f"  [OK] Recreated vectordb directory")
        except Exception as e:
            print(f"  [WARN] Could not remove vectordb directory: {e}")
            print(f"  [INFO] This may cause 'different settings' error - will try to continue")
            # Try to continue anyway - might work if directory is empty
    else:
        # Create directory if it doesn't exist
        os.makedirs(vectordb_path, mode=0o755, exist_ok=True)
        print(f"  [OK] Created vectordb directory")
    
    # CRITICAL: Test SQLite write capability before ChromaDB tries to use it
    # SQLite has specific requirements that regular file writes don't catch
    print(f"  [INFO] Testing SQLite write capability...")
    try:
        import sqlite3
        # Check SQLite version (ChromaDB requires 3.35.0+)
        sqlite_version = sqlite3.sqlite_version
        print(f"  [INFO] SQLite version: {sqlite_version}")
        version_parts = [int(x) for x in sqlite_version.split('.')]
        if version_parts[0] < 3 or (version_parts[0] == 3 and version_parts[1] < 35):
            print(f"  [WARN] SQLite version may be too old (ChromaDB requires 3.35.0+)")
        
        test_sqlite = os.path.join(vectordb_path, 'test_sqlite.db')
        conn = sqlite3.connect(test_sqlite)
        # Try setting journal mode to DELETE (more compatible with some filesystems)
        # WAL mode can cause issues with some volume mounts
        try:
            conn.execute("PRAGMA journal_mode=DELETE")
            print(f"  [INFO] Set SQLite journal mode to DELETE")
        except:
            pass  # Some SQLite versions/configurations don't support this
        
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        cursor.execute("INSERT INTO test (id) VALUES (1)")
        conn.commit()
        conn.close()
        os.remove(test_sqlite)
        print(f"  [OK] SQLite write test passed")
    except Exception as sqlite_e:
        print(f"  [ERROR] SQLite write test failed: {sqlite_e}")
        print(f"  [ERROR] This indicates a SQLite-specific permission issue")
        print(f"  [ERROR] Railway volumes may have restrictions on SQLite journal/WAL files")
        raise Exception(f"Cannot write SQLite database files: {sqlite_e}")
    
    # CRITICAL: Ensure directory has correct permissions and is empty
    # ChromaDB's Rust bindings need to create the SQLite file themselves
    # Pre-creating it might cause issues if ChromaDB expects to create it fresh
    print(f"  [INFO] Ensuring vectordb directory is ready for ChromaDB...")
    sqlite_file = os.path.join(vectordb_path, 'chroma.sqlite3')
    
    # Remove any pre-existing SQLite file - ChromaDB needs to create it
    if os.path.exists(sqlite_file):
        try:
            os.remove(sqlite_file)
            print(f"  [INFO] Removed pre-existing SQLite file (ChromaDB will create it)")
        except Exception as e:
            print(f"  [WARN] Could not remove pre-existing SQLite file: {e}")
    
    # Ensure directory has world-writable permissions (777) to allow ChromaDB's Rust bindings
    # Railway volumes might have permission restrictions that require this
    try:
        import stat
        os.chmod(vectordb_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 777
        print(f"  [OK] Set directory permissions to 777 (world-writable)")
    except Exception as e:
        print(f"  [WARN] Could not set directory permissions: {e}")
    
    # Use same settings as QueryEngine (no explicit settings = defaults)
    # This avoids "different settings" error when ChromaDB was initialized elsewhere
    print(f"  [INFO] Creating ChromaDB client...")
    client = chromadb.PersistentClient(path=vectordb_path)
    
    # Delete existing collection (if it somehow still exists)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"  [INFO] Deleted existing collection")
    except:
        pass
    
    # Check what files ChromaDB creates before collection creation
    print(f"  [INFO] Files in vectordb before collection creation:")
    try:
        for f in os.listdir(vectordb_path):
            filepath = os.path.join(vectordb_path, f)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                perms = oct(os.stat(filepath).st_mode)[-3:]
                print(f"    - {f} ({size} bytes, permissions: {perms})")
    except Exception as list_e:
        print(f"    [WARN] Could not list files: {list_e}")
    
    print(f"  [INFO] Creating new collection '{COLLECTION_NAME}'...")
    try:
        collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"  [OK] Collection created")
        
        # Check files after collection creation
        print(f"  [INFO] Files in vectordb after collection creation:")
        try:
            for f in os.listdir(vectordb_path):
                filepath = os.path.join(vectordb_path, f)
                if os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    perms = oct(os.stat(filepath).st_mode)[-3:]
                    print(f"    - {f} ({size} bytes, permissions: {perms})")
        except Exception as list_e:
            print(f"    [WARN] Could not list files: {list_e}")
        
        # Fix permissions on SQLite database file and any related files
        # Set to world-writable (666) to ensure ChromaDB's Rust bindings can write
        if os.path.exists(sqlite_file):
            try:
                import stat
                # Set to world-writable (666) - Railway volumes may need this
                os.chmod(sqlite_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
                print(f"  [OK] Fixed permissions on SQLite database (666)")
            except Exception as e:
                print(f"  [WARN] Could not fix SQLite permissions: {e}")
        
        # Also fix permissions on any WAL or journal files ChromaDB might create
        for suffix in ['.sqlite3-wal', '.sqlite3-shm', '.sqlite3-journal']:
            wal_file = sqlite_file + suffix
            if os.path.exists(wal_file):
                try:
                    os.chmod(wal_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
                    print(f"  [OK] Fixed permissions on {suffix} file (666)")
                except Exception as e:
                    print(f"  [WARN] Could not fix permissions on {suffix}: {e}")
    except Exception as e:
        error_msg = str(e)
        if 'readonly' in error_msg.lower() or '1032' in error_msg:
            print(f"  [ERROR] Readonly database error - checking volume permissions...")
            # Check if we can write to the directory
            test_file = os.path.join(vectordb_path, 'test_write.tmp')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print(f"  [INFO] Directory is writable, but ChromaDB SQLite creation failed")
                print(f"  [INFO] This suggests ChromaDB's Rust bindings have different permission requirements")
                print(f"  [INFO] SQLite test passed, so this is ChromaDB-specific")
            except Exception as perm_e:
                print(f"  [ERROR] Cannot write to directory: {perm_e}")
        
        # List files to see what ChromaDB tried to create
        print(f"  [ERROR] Files in vectordb after failed collection creation:")
        try:
            for f in os.listdir(vectordb_path):
                filepath = os.path.join(vectordb_path, f)
                if os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    perms = oct(os.stat(filepath).st_mode)[-3:]
                    print(f"    - {f} ({size} bytes, permissions: {perms})")
        except Exception as list_e:
            print(f"    [WARN] Could not list files: {list_e}")
        
        raise
    
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


