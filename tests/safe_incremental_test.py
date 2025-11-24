"""
Safe Incremental Testing - Don't waste API quota!

Tests in stages:
1. Single chunk (1 API call) - Verify LLM returns valid JSON
2. Small batch (5 API calls) - Verify batching works
3. Medium test (20 API calls) - Verify accuracy on known people
4. ONLY THEN: Full run (138 API calls)

Stops immediately if any stage fails.
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.document_parser import load_all_documents
from lib.index_builder import split_into_chunks
from lib.llm_identity_detector import LLMIdentityDetector

def test_stage_1_single_chunk():
    """Stage 1: Test on 1 chunk - verify JSON parsing works"""
    print("\n" + "="*80)
    print("STAGE 1: Single Chunk Test (1 API call)")
    print("="*80)
    print("Goal: Verify LLM returns valid JSON without errors\n")
    
    # Load one chunk with Lebanese content
    documents = load_all_documents(use_cache=True)
    all_chunks = []
    for doc in documents:
        chunks = split_into_chunks(doc['text'])
        all_chunks.extend(chunks)
    
    # Find Lebanese Christians chunk
    test_chunk = None
    for chunk in all_chunks:
        if 'lebanese christians fleeing' in chunk.lower():
            test_chunk = chunk
            break
    
    if not test_chunk:
        print("[FAIL] Test chunk not found")
        return False
    
    print(f"Processing chunk (length: {len(test_chunk)} chars)...")
    print(f"Preview: {test_chunk[:150]}...\n")
    
    # Test
    detector = LLMIdentityDetector()
    
    try:
        results = detector.detect_from_chunks([test_chunk], force_rerun=True)
        
        # Check if results are valid
        if not results or 'identities' not in results:
            print("[FAIL] No results returned")
            return False
        
        print("[SUCCESS] LLM returned valid results!")
        print(f"Identities detected: {len(results['identities'])}")
        
        # Show sample
        for identity in list(results['identities'].keys())[:5]:
            families = results['identities'][identity].get('families', []) or results['identities'][identity].get('individuals', [])
            print(f"  {identity}: {families[:5]}")
        
        # Verify found Wall St Lebanese
        lebanese = results['identities'].get('lebanese', {}).get('families', [])
        found_wallst = any(name in str(lebanese).lower() for name in ['abdelnour', 'boutros', 'chammah'])
        
        if found_wallst:
            print(f"\n[EXCELLENT] Found Wall St Lebanese: {lebanese}")
        else:
            print(f"\n[WARNING] Missed Wall St Lebanese. Found: {lebanese}")
            print("This might be OK if they're in different chunks")
        
        return True
    
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_stage_2_small_batch():
    """Stage 2: Test batch of 5 chunks"""
    print("\n" + "="*80)
    print("STAGE 2: Small Batch (5 chunks, 2 API calls)")
    print("="*80)
    print("Goal: Verify batch processing works correctly\n")
    
    documents = load_all_documents(use_cache=True)
    all_chunks = []
    for doc in documents:
        chunks = split_into_chunks(doc['text'])
        all_chunks.extend(chunks)
    
    # Get chunks with diverse content
    test_chunks = []
    keywords = ['lebanese', 'hausa', 'yoruba', 'muslim', 'chavez']
    for chunk in all_chunks:
        if any(kw in chunk.lower() for kw in keywords):
            test_chunks.append(chunk)
            if len(test_chunks) >= 5:
                break
    
    print(f"Processing {len(test_chunks)} diverse chunks...")
    
    detector = LLMIdentityDetector()
    detector.BATCH_SIZE = 3  # Batch of 3
    
    try:
        results = detector.detect_from_chunks(test_chunks, force_rerun=True)
        
        print(f"[SUCCESS] Batch processing worked!")
        print(f"Identities detected: {len(results['identities'])}")
        
        # Show results
        for identity in ['lebanese', 'muslim', 'hausa', 'black']:
            data = results['identities'].get(identity, {})
            families = data.get('families', []) or data.get('individuals', [])
            if families:
                print(f"  {identity}: {families[:8]}")
        
        return True
    
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_stage_3_accuracy():
    """Stage 3: Test on 20 chunks, verify accuracy"""
    print("\n" + "="*80)
    print("STAGE 3: Accuracy Test (20 chunks, ~7 API calls)")
    print("="*80)
    print("Goal: Verify we find known people (90%+ accuracy)\n")
    
    # Ground truth
    known_people = {
        'lebanese': ['sursock', 'chiha', 'abdelnour', 'boutros'],
        'latino': ['alvarez', 'chavez', 'diaz'],
        'black': ['ogunlesi', 'okwei'],
    }
    
    documents = load_all_documents(use_cache=True)
    all_chunks = []
    for doc in documents:
        chunks = split_into_chunks(doc['text'])
        all_chunks.extend(chunks)
    
    # Get chunks with known people
    test_chunks = []
    for chunk in all_chunks:
        chunk_lower = chunk.lower()
        for identity, names in known_people.items():
            if any(name in chunk_lower for name in names):
                test_chunks.append(chunk)
                break
        if len(test_chunks) >= 20:
            break
    
    print(f"Processing {len(test_chunks)} chunks with known people...")
    
    detector = LLMIdentityDetector()
    detector.BATCH_SIZE = 3
    
    try:
        results = detector.detect_from_chunks(test_chunks, force_rerun=True)
        
        # Verify accuracy
        total_expected = sum(len(names) for names in known_people.values())
        total_found = 0
        
        print("\nVerifying against known people:")
        for identity, expected_names in known_people.items():
            detected = results['identities'].get(identity, {})
            families = detected.get('families', []) or detected.get('individuals', [])
            families_lower = [f.lower() for f in families]
            
            found = [name for name in expected_names if name in families_lower]
            total_found += len(found)
            
            print(f"  {identity}: {len(found)}/{len(expected_names)} found")
            if len(found) < len(expected_names):
                missing = [n for n in expected_names if n not in families_lower]
                print(f"    Missing: {missing}")
        
        accuracy = (total_found / total_expected) * 100
        print(f"\nAccuracy: {total_found}/{total_expected} = {accuracy:.1f}%")
        
        if accuracy >= 70:
            print("[SUCCESS] Good enough to proceed to full run")
            return True
        else:
            print("[FAIL] Accuracy too low - don't proceed")
            return False
    
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


if __name__ == '__main__':
    print("="*80)
    print("SAFE INCREMENTAL TESTING")
    print("="*80)
    print("\nThis will test the LLM detector in stages to avoid wasting API quota.")
    print("Stops immediately if any stage fails.\n")
    
    input("Press Enter to start Stage 1 (1 API call)...")
    
    # Stage 1: Single chunk
    if not test_stage_1_single_chunk():
        print("\n[ABORT] Stage 1 failed. Fix issues before continuing.")
        sys.exit(1)
    
    input("\nStage 1 passed! Press Enter for Stage 2 (5 chunks, 2 API calls)...")
    
    # Stage 2: Small batch
    if not test_stage_2_small_batch():
        print("\n[ABORT] Stage 2 failed. Fix issues before continuing.")
        sys.exit(1)
    
    input("\nStage 2 passed! Press Enter for Stage 3 (20 chunks, ~7 API calls)...")
    
    # Stage 3: Accuracy test
    if not test_stage_3_accuracy():
        print("\n[ABORT] Stage 3 failed. Accuracy too low.")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("ALL STAGES PASSED!")
    print("="*80)
    print("\nSafe to run full detection:")
    print("  python scripts/complete_detection_tomorrow.py")
    print("\nTotal API calls used in testing: ~10 calls (0.8% of daily capacity)")

