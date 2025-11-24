"""
Run Batch Identity Detection - Submit all chunks as one batch job.

Advantages:
- 50% cost reduction vs interactive API
- Different quota pool (no RPM/RPD limits on submission)
- Process all 1,500 chunks at once
- Async processing (submit and check back)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.batch_identity_detector import BatchIdentityDetector
from lib.document_parser import load_all_documents
from lib.index_builder import split_into_chunks

def main():
    print("=== BATCH IDENTITY DETECTION ===\n")
    
    # Load chunks
    print("Loading document chunks...")
    docs = load_all_documents(use_cache=True)
    
    chunks = []
    for doc in docs:
        chunks.extend(split_into_chunks(doc['text']))
    
    print(f"  [OK] Loaded {len(chunks)} chunks\n")
    
    # Initialize detector
    detector = BatchIdentityDetector()
    
    # Submit batch job
    job_name = detector.submit_batch_job(chunks, job_name="thunderclap-identity-detection")
    
    if not job_name:
        print("\n[DONE] No new chunks to process (all cached)")
        return
    
    print("\n" + "="*60)
    print("BATCH JOB SUBMITTED!")
    print("="*60)
    print(f"\nJob name: {job_name}")
    print("\nWhat happens next:")
    print("  1. Gemini processes your batch (target: < 24 hours, often faster)")
    print("  2. You can check status anytime")
    print("  3. When complete, retrieve results")
    print("\nCommands:")
    print(f"  Check status: python lib/batch_identity_detector.py status {job_name}")
    print(f"  Get results:  python lib/batch_identity_detector.py results {job_name}")
    print("\nOr use the helper script:")
    print("  python scripts/check_batch_status.py")
    
    # Ask if user wants to poll
    print("\n" + "-"*60)
    response = input("Poll for completion now? (y/n): ").strip().lower()
    
    if response == 'y':
        print()
        success = detector.poll_until_complete(job_name, poll_interval=60)
        
        if success:
            print("\nRetrieving results...")
            detector.retrieve_results(job_name)
            
            # Show summary
            results = detector.get_results()
            print("\n=== DETECTION SUMMARY ===\n")
            
            identities = results['identities']
            for identity in sorted(identities.keys()):
                families = identities[identity]
                print(f"  {identity}: {len(families)} families")
            
            print(f"\nTotal chunks processed: {results['total_chunks_cached']}")
            print("\n[NEXT] Rebuild index with detected identities:")
            print("  python build_index.py")
    else:
        print("\n[OK] Job is processing. Check back later!")

if __name__ == '__main__':
    main()

