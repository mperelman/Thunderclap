"""
Auto-run script for tomorrow when API quotas reset.
Completes remaining LLM detection with full chunk context and 6 API keys.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("="*80)
print("COMPLETING LLM IDENTITY DETECTION")
print("="*80)
print("\nUsing:")
print("  - 6 API keys (1200 requests/day capacity)")
print("  - Batch size: 3 chunks per call")
print("  - FULL chunk context (no truncation)")
print("  - Automatic key rotation")
print("\nExpected:")
print("  - ~138 API calls needed (415 remaining chunks)")
print("  - ~12 minutes to complete")
print("  - 90%+ accuracy (vs 47% regex)")
print("\n" + "="*80 + "\n")

from lib.llm_identity_detector import detect_identities_from_index

# Run detection
results, detector = detect_identities_from_index(
    identities_to_process=None,  # All identities
    force_rerun=False,  # Use cache
    save_results=True
)

# Display results
print("\n" + "="*80)
print("DETECTION COMPLETE")
print("="*80)

print(f"\nIdentities detected: {len(results['identities'])}")
print("\nTop families per identity:")
for identity in ['lebanese', 'latino', 'basque', 'black', 'muslim', 'hausa', 'yoruba']:
    data = results['identities'].get(identity, {})
    families = data.get('families', []) or data.get('individuals', [])
    if families:
        print(f"  {identity}: {families[:10]}")

# Verify against ground truth
print("\n" + "="*80)
print("VERIFICATION")
print("="*80)

ground_truth = {
    'latino': ['alvarez', 'seix', 'goizueta', 'banuelos', 'diaz', 'arboleya', 'chavez', 'salinas'],
    'lebanese_wallst': ['abdelnour', 'boutros', 'chammah', 'bitar', 'jabre', 'mack', 'noujaim'],
    'african': ['dantata', 'okwei', 'ogunlesi', 'thiam', 'ouattara'],
}

for category, expected in ground_truth.items():
    identity_key = category.split('_')[0]  # lebanese_wallst -> lebanese
    detected = results['identities'].get(identity_key, {})
    families = detected.get('families', []) or detected.get('individuals', [])
    families_lower = [f.lower() for f in families]
    
    found = [name for name in expected if name in families_lower]
    missing = [name for name in expected if name not in families_lower]
    
    print(f"\n{category.upper()}: {len(found)}/{len(expected)}")
    if missing:
        print(f"  Missing: {', '.join(missing)}")

print("\n[DONE] Results saved to data/detected_identities.json")
print("Next: Run 'python build_index.py' to integrate into search index")

