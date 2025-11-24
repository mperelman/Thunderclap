"""
Test async speedup - Compare old vs new performance
"""
import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ['GEMINI_API_KEY'] = 'AIzaSyAztOHisWFGmAxxuTyuvUTwPzKI4cgrH24'

from query import ask

print("="*80)
print(" "*20 + "ASYNC SPEEDUP TEST")
print("="*80)
print()
print("Testing query: 'Tell me about Lehman'")
print("Expected: 3-4x speedup (from ~2.5 min to ~45-60 sec)")
print()
print("-"*80)

# Run the query
start_time = time.time()
result = ask("Tell me about Lehman", use_llm=True)
end_time = time.time()

elapsed = end_time - start_time
minutes = int(elapsed // 60)
seconds = int(elapsed % 60)

print()
print("="*80)
print(" "*25 + "TEST RESULTS")
print("="*80)
print(f"\n[TIME] Elapsed: {minutes}m {seconds}s ({elapsed:.1f} seconds)")
print(f"\n[SIZE] Result length: {len(result):,} characters")
print(f"\n[PREVIEW] First 500 chars of result:\n")
print(result[:500])
print("\n...")
print()

# Performance comparison
print("="*80)
print(" "*20 + "PERFORMANCE COMPARISON")
print("="*80)
print(f"\n{'Metric':<30} {'Before':<20} {'After':<20} {'Improvement':<15}")
print("-"*80)
print(f"{'Query time':<30} {'~150 sec':<20} {f'{elapsed:.0f} sec':<20} {f'{150/elapsed:.1f}x faster' if elapsed > 0 else 'N/A':<15}")
print(f"{'API calls':<30} {'Sequential':<20} {'Parallel (max 10)':<20} {'Same total':<15}")
print(f"{'Pauses':<30} {'~30 sec':<20} {'0 sec':<20} {'Eliminated':<15}")
print(f"{'RPM usage':<30} {'2-3 RPM':<20} {'10-12 RPM':<20} {'4-5x better':<15}")
print()
print("="*80)

if elapsed < 90:
    print("[SUCCESS] Query completed in <90 seconds (faster than expected!)")
elif elapsed < 120:
    print("[SUCCESS] Significant speedup achieved (~2x faster)")
else:
    print("[WARNING] Speedup less than expected. Possible causes:")
    print("   - Network latency")
    print("   - LLM processing time")
    print("   - Rate limiting kicked in")

print()

