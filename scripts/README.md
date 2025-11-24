# Thunderclap Scripts

Utility scripts for maintaining and verifying the Thunderclap AI system.

## Verification Scripts

### verify_identity_index.py
Verifies that identity detection results are properly integrated into the search index.

**Usage:**
```bash
python scripts/verify_identity_index.py
```

**Tests:**
- sunni, alawite, black, gay, quaker identities
- Compares detection results vs. index entries
- Shows overlap statistics

**Example Output:**
```
VERIFICATION: SUNNI
============================================================
1. Identity Detection Results:
   sunni: 43 chunks detected
   
2. Search Index Results:
   sunni: 140 chunks in index
   
✅ INDEX WORKING: 43 detected + 97 text mentions = 140 total
```

### show_all_identities.py
Displays all detected identities sorted by chunk count.

**Usage:**
```bash
python scripts/show_all_identities.py
```

**Output:**
```
=== ALL 342 IDENTITIES ===

christian                      1,494 chunks
jewish                         1,480 chunks
american                       1,446 chunks
british                        1,426 chunks
...
```

## Analysis Scripts

### analyze_jewish_volume.py
Analyzes the volume and distribution of Jewish banking history content.

**Usage:**
```bash
python scripts/analyze_jewish_volume.py
```

## Batch Processing Scripts

### run_batch_detection.py
Submit identity detection job to Gemini Batch API (50% cost reduction, different quotas).

**Usage:**
```bash
python scripts/run_batch_detection.py
```

**Note:** Batch API may have different model availability. Check Google AI Studio for supported models.

### check_batch_status.py
Check status of submitted batch jobs.

**Usage:**
```bash
python scripts/check_batch_status.py <batch_job_id>
```

## Detection Scripts

### run_identity_detection.py
Runs Steps 3-4 of identity detection (surname search + index building).

**Prerequisites:**
- LLM detection (Steps 1-2) must be completed
- `data/llm_identity_cache.json` must exist

**Usage:**
```bash
python scripts/run_identity_detection.py
```

**Output:**
- `data/identity_detection_v3.json`
- Statistics on surnames, identities, and chunk mappings

**Next Step:**
```bash
python build_index.py  # Rebuild main index with identity integration
```

## Maintenance

### When to Run Scripts

**After Document Changes:**
1. `python build_index.py` (includes identity detection)

**After Detection Logic Changes:**
1. Delete cache: `del data\llm_identity_cache.json`
2. `python build_index.py` (re-runs detection with new logic)

**To Verify System:**
1. `python scripts/verify_identity_index.py`
2. `python scripts/show_all_identities.py`

**To Analyze Content:**
1. `python scripts/analyze_jewish_volume.py`

## Script Dependencies

All scripts require:
```python
import sys
sys.path.insert(0, '.')  # Add project root to path
```

And depend on:
- `lib/` modules
- `data/` files (indices, detection results, cache)
- `.env` file with API keys (for LLM-based scripts)

