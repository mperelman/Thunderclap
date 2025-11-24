"""
Check status of batch detection job and retrieve results when ready.
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.batch_identity_detector import BatchIdentityDetector

def main():
    # Load job info
    job_info_file = Path('temp/batch_job_info.json')
    
    if not job_info_file.exists():
        print("[ERROR] No batch job info found.")
        print("Submit a batch job first:")
        print("  python scripts/run_batch_detection.py")
        return
    
    with open(job_info_file) as f:
        job_info = json.load(f)
    
    job_name = job_info['job_name']
    
    print(f"=== BATCH JOB STATUS ===\n")
    print(f"Job: {job_name}")
    print(f"Submitted: {job_info.get('num_requests', 'unknown')} requests\n")
    
    # Check status
    detector = BatchIdentityDetector()
    status = detector.check_job_status(job_name)
    
    if 'error' in status:
        print(f"[ERROR] {status['error']}")
        return
    
    state = status['state']
    print(f"State: {state}")
    
    if 'stats' in status:
        stats = status['stats']
        print(f"\nProgress:")
        print(f"  Total: {stats['total']}")
        print(f"  Succeeded: {stats['succeeded']}")
        print(f"  Failed: {stats['failed']}")
    
    if status['completed']:
        print("\n" + "="*60)
        
        if state == 'JOB_STATE_SUCCEEDED':
            print("[COMPLETE] Job finished successfully!")
            print("="*60)
            
            response = input("\nRetrieve results now? (y/n): ").strip().lower()
            
            if response == 'y':
                print()
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
            print(f"[FAILED] Job ended with state: {state}")
            print("="*60)
    else:
        print("\n[PENDING] Job still processing...")
        print("\nCheck again later with:")
        print("  python scripts/check_batch_status.py")

if __name__ == '__main__':
    main()


