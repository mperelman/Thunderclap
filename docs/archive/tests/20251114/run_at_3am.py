"""
Run this at 3:00am ET when quota resets.
Conservative testing - won't waste quota.
"""
import sys
sys.path.insert(0, '.')

print("="*70)
print("TESTING FIXED LLM DETECTOR (Conservative)")
print("="*70)
print()

# Step 1: Test API key works (1 request)
print("Step 1: Testing API key...")
try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    import os
    
    load_dotenv(override=True)
    key = os.getenv('GEMINI_API_KEY_1')
    
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content("Say: quota reset")
    
    print(f"  [SUCCESS] API working! Response: {response.text}")
    print()

except Exception as e:
    print(f"  [FAILED] API still exhausted: {e}")
    print("\n[EXIT] Wait longer for quota reset")
    sys.exit(1)

# Step 2: Test on ONLY 5 chunks (very conservative - ~1 API call)
print("Step 2: Testing detector on 5 sample chunks...")
print("  (This uses only ~1 API request)")
print()

try:
    from lib.document_parser import load_all_documents
    from lib.index_builder import split_into_chunks
    from lib.llm_identity_detector import LLMIdentityDetector
    
    # Load just a few chunks
    docs = load_all_documents(use_cache=True)
    all_chunks = []
    for doc in docs[:1]:  # Just first document
        all_chunks.extend(split_into_chunks(doc['text']))
    
    # Take only 5 chunks
    sample_chunks = all_chunks[:5]
    
    print(f"  Testing on {len(sample_chunks)} chunks...")
    
    # Run detector
    detector = LLMIdentityDetector()
    results = detector.detect_from_chunks(sample_chunks, force_rerun=True)
    
    identities = results.get('identities', {})
    
    print(f"\n  [SUCCESS] Detected {len(identities)} identity types!")
    print()
    
    for identity in sorted(identities.keys())[:10]:
        families = identities[identity]
        print(f"    {identity}: {len(families)} families - {list(families.keys())[:3]}")
    
    if len(identities) > 10:
        print(f"    ... and {len(identities) - 10} more")
    
    print()
    
    if len(identities) >= 5:
        print("  [EXCELLENT] Detector is working! Much better than 99.7% failure!")
        print()
        print("  Ready to process all 1,516 chunks?")
        response = input("  Run full detection? (y/n): ").strip().lower()
        
        if response == 'y':
            print("\n  [RUNNING] Full detection on all 1,516 chunks...")
            print("  (This will use ~75 API requests with proper key rotation)")
            print()
            
            all_chunks_full = []
            for doc in docs:
                all_chunks_full.extend(split_into_chunks(doc['text']))
            
            results_full = detector.detect_from_chunks(all_chunks_full, force_rerun=True)
            
            print("\n  [COMPLETE] Full detection finished!")
            print(f"  Detected {len(results_full.get('identities', {}))} identity types")
            print("\n  [NEXT] Rebuild index:")
            print("    python build_index.py")
        else:
            print("\n  [OK] Stopped. Run full detection later with:")
            print("    python lib/llm_identity_detector.py")
    else:
        print("  [WARNING] Still low detection rate. Check prompt or data.")

except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()


