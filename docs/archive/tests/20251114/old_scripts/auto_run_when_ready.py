"""
Auto-run LLM detection when API quota resets.

This script:
1. Waits until midnight Pacific Time (when quotas reset)
2. Runs safe incremental test (10 API calls)
3. If successful, runs full detection (138 API calls)
4. Rebuilds index with results

Just run this now and let it wait!
"""
import sys
import os
import time
from datetime import datetime, timezone
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_pacific_time():
    """Get current time in Pacific timezone."""
    try:
        import pytz
        pt_tz = pytz.timezone('America/Los_Angeles')
        return datetime.now(pt_tz)
    except:
        # Fallback: assume PT is UTC-8 (PST) or UTC-7 (PDT)
        from datetime import timedelta
        utc_now = datetime.now(timezone.utc)
        # Assume PST (UTC-8) for November
        pt_now = utc_now - timedelta(hours=8)
        return pt_now

def wait_until_midnight_pt():
    """Wait until midnight Pacific Time."""
    pt_now = get_pacific_time()
    
    print(f"Current Pacific Time: {pt_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Calculate next midnight PT
    from datetime import timedelta
    if pt_now.hour >= 0:  # Already past midnight
        next_midnight = pt_now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    else:
        next_midnight = pt_now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    wait_seconds = (next_midnight - pt_now).total_seconds()
    
    if wait_seconds <= 0:
        print("[READY] Quotas should be reset!")
        return
    
    wait_minutes = wait_seconds / 60
    wait_hours = wait_minutes / 60
    
    print(f"Next quota reset: {next_midnight.strftime('%Y-%m-%d %H:%M:%S')} PT")
    print(f"Time to wait: {wait_hours:.1f} hours ({wait_minutes:.0f} minutes)")
    print(f"\nWaiting... (you can close this and run later, or let it wait)")
    
    # Wait with progress updates
    while wait_seconds > 0:
        if wait_seconds > 300:  # More than 5 minutes
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] {wait_minutes:.0f} minutes remaining...")
            time.sleep(300)  # Check every 5 minutes
            pt_now = get_pacific_time()
            wait_seconds = (next_midnight - pt_now).total_seconds()
            wait_minutes = wait_seconds / 60
        else:
            time.sleep(wait_seconds)
            break
    
    print(f"\n[READY] Midnight PT reached! Starting detection...")

def run_safe_test():
    """Run safe incremental test."""
    print("\n" + "="*80)
    print("RUNNING SAFE INCREMENTAL TEST")
    print("="*80)
    
    result = subprocess.run(
        [sys.executable, 'scripts/safe_incremental_test.py'],
        capture_output=False,
        text=True
    )
    
    return result.returncode == 0

def run_full_detection():
    """Run full LLM detection."""
    print("\n" + "="*80)
    print("RUNNING FULL DETECTION")
    print("="*80)
    
    result = subprocess.run(
        [sys.executable, 'scripts/complete_detection_tomorrow.py'],
        capture_output=False,
        text=True
    )
    
    return result.returncode == 0

def rebuild_index():
    """Rebuild search index."""
    print("\n" + "="*80)
    print("REBUILDING INDEX")
    print("="*80)
    
    result = subprocess.run(
        [sys.executable, 'build_index.py'],
        capture_output=False,
        text=True
    )
    
    return result.returncode == 0


if __name__ == '__main__':
    print("="*80)
    print("AUTOMATED LLM DETECTION - SCHEDULED RUN")
    print("="*80)
    print()
    
    # Wait for quota reset
    wait_until_midnight_pt()
    
    # Run safe test first
    print("\n[STAGE 1/3] Safe Incremental Test (10 API calls)...")
    if not run_safe_test():
        print("\n[ABORT] Safe test failed. Not running full detection.")
        print("Check errors above and fix before retrying.")
        sys.exit(1)
    
    print("\n[SUCCESS] Safe test passed!")
    
    # Ask to proceed
    response = input("\nProceed with full detection? (y/n): ")
    if response.lower() != 'y':
        print("[STOPPED] User chose not to proceed.")
        sys.exit(0)
    
    # Run full detection
    print("\n[STAGE 2/3] Full LLM Detection (138 API calls, ~12 min)...")
    if not run_full_detection():
        print("\n[ERROR] Full detection failed.")
        sys.exit(1)
    
    print("\n[SUCCESS] Detection complete!")
    
    # Rebuild index
    print("\n[STAGE 3/3] Rebuilding search index...")
    if not rebuild_index():
        print("\n[ERROR] Index rebuild failed.")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("ALL COMPLETE!")
    print("="*80)
    print("\nYou can now query with improved accuracy:")
    print("  python query.py \"tell me about lebanese bankers\"")

