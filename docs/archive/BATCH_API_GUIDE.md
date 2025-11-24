# Batch API Identity Detection - Quick Start Guide

## What Is This?

The Batch API is a better way to run identity detection:

### Interactive API (Current)
- ❌ Rate limits: 15 RPM, 200 RPD per key
- ❌ All 6 keys exhausted today
- ❌ Full price
- ⏱️ Real-time responses

### Batch API (New)
- ✅ No RPM limits on submission
- ✅ Different quota pool (likely not exhausted)
- ✅ **50% cost reduction**
- ✅ Process all 1,500 chunks at once
- ⏱️ Async (< 24 hours, often much faster)

---

## How To Use

### Step 1: Submit Batch Job

```bash
python scripts/run_batch_detection.py
```

This will:
1. Load all 1,500 chunks
2. Skip chunks already in cache
3. Create JSONL file with requests
4. Upload to Gemini
5. Submit batch job
6. Give you a job name to track

**Cost:** 50% of interactive API pricing  
**Time:** Usually completes in a few hours (target < 24 hours)

---

### Step 2: Check Status

```bash
python scripts/check_batch_status.py
```

Or manually:

```bash
python lib/batch_identity_detector.py status <job_name>
```

This shows:
- Current state (PENDING, RUNNING, SUCCEEDED, etc.)
- Progress (N/M requests completed)
- Any errors

---

### Step 3: Retrieve Results

Once status shows `JOB_STATE_SUCCEEDED`:

```bash
python scripts/check_batch_status.py
# It will prompt to retrieve results
```

Or manually:

```bash
python lib/batch_identity_detector.py results <job_name>
```

This will:
1. Download results file from Gemini
2. Parse all identity classifications
3. Update cache (`data/llm_identity_cache.json`)
4. Show summary of detected identities

---

### Step 4: Rebuild Index

```bash
python build_index.py
```

This integrates the detected identities into the search index.

---

## Testing Right Now

Even though your interactive API keys are exhausted, the Batch API uses a **different quota system**.

**Try it now:**

```bash
cd C:\Users\perel\OneDrive\Apps\thunderclap-ai
python scripts/run_batch_detection.py
```

If it works, you'll see:
```
[SUCCESS] Batch job submitted!
Job name: batches/xxxxxxxxx
```

Then check back in a few hours to retrieve results.

---

## Files Created

1. `lib/batch_identity_detector.py` - Main batch detector module
2. `scripts/run_batch_detection.py` - Easy submission script
3. `scripts/check_batch_status.py` - Check job status
4. `temp/batch_requests.jsonl` - Request file (temporary)
5. `temp/batch_job_info.json` - Tracks current job

---

## Why This Works Better

### Problem with Interactive API:
- Each API call processes 1-20 chunks
- 75+ API calls needed for 1,500 chunks
- Must wait 4-5 seconds between calls (rate limiting)
- Exhausts daily quota quickly (200 RPD)
- Keys #3-7 were never tried (rotation bug)

### Solution with Batch API:
- **One submission** for all 1,500 chunks
- No waiting between chunks
- Different quota system
- 50% cheaper
- Processes asynchronously

**This is the professional way to do large-scale LLM processing.**

---

## Next Steps

1. **Try it now**: `python scripts/run_batch_detection.py`
2. **If it works**: Wait for completion, retrieve results
3. **If it fails**: We know Batch API also exhausted (rare, but possible)

Ready to try?


