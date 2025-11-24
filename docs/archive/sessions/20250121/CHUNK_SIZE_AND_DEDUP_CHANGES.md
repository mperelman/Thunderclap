# Chunk Size Reduction & Deduplication Changes

**Date:** 2025-01-XX  
**Status:** ✅ Completed

---

## Changes Made

### 1. ✅ Reduced Chunk Size

**File:** `lib/config.py`

**Before:**
```python
CHUNK_SIZE = 1000  # words
CHUNK_OVERLAP = 200  # words
ESTIMATED_WORDS_PER_CHUNK = 1000
```

**After:**
```python
CHUNK_SIZE = 400  # words
CHUNK_OVERLAP = 100  # words
ESTIMATED_WORDS_PER_CHUNK = 400
MAX_WORDS_PER_REQUEST = 600000  # ~800K tokens / 1.3
```

**Impact:**
- Smaller chunks = better granularity for retrieval
- More chunks total (will need to rebuild index)
- Better precision for finding specific information

---

### 2. ✅ Added Deduplication & Combination Logic

**File:** `lib/query_engine.py`

**New Function:** `_deduplicate_and_combine_chunks()`

**What it does:**

#### Step 1: Remove Exact Duplicates
- Compares normalized text (lowercase, stripped)
- Removes chunks with identical content
- Preserves first occurrence

#### Step 2: Merge Overlapping Chunks
Detects and merges chunks that overlap due to `CHUNK_OVERLAP`:
- **End-to-start overlap**: If end of chunk1 matches start of chunk2
  - Merges: `chunk1 + chunk2 (without duplicate overlap)`
- **Start-to-end overlap**: If start of chunk1 matches end of chunk2
  - Merges: `chunk2 + chunk1 (without duplicate overlap)`
- **Substring containment**: If one chunk is contained in another
  - Keeps the larger chunk, discards the smaller

#### Step 3: Combine into Batches
- Groups chunks up to `MAX_WORDS_PER_REQUEST` (600K words)
- Combines multiple chunks into single requests when possible
- Reduces API call count while staying under token limits

**Called:** Before sending chunks to LLM (line 522)

---

## How It Works

### Example Flow:

**Input:** 10 overlapping chunks (400 words each, 100-word overlap)

1. **Deduplication**: Removes 2 exact duplicates → 8 chunks
2. **Merging**: Detects 3 overlapping pairs → merges to 5 chunks
3. **Combination**: Groups 5 chunks into 1 batch (fits in 600K word limit) → 1 API call

**Result:** 10 chunks → 1 API call (instead of 10 separate calls)

---

## Benefits

✅ **Fewer API calls** - Combines chunks intelligently  
✅ **No duplication** - Removes redundant content  
✅ **Stays under limits** - Respects token/word limits  
✅ **Better efficiency** - Maximizes context per request  
✅ **Smaller chunks** - Better retrieval granularity (after rebuild)  

---

## Next Steps

**To apply new chunk size:**

1. **Rebuild index** (required - existing DB has 1000-word chunks):
   ```bash
   python build_index.py
   ```

2. **Verify deduplication works**:
   - Test with a query that returns many chunks
   - Check console output for `[DEDUP]` and `[MERGE]` messages

---

## Configuration Summary

```python
# Indexing (for future rebuilds)
CHUNK_SIZE = 400  # words per chunk
CHUNK_OVERLAP = 100  # words overlap between chunks

# Processing (current)
ESTIMATED_WORDS_PER_CHUNK = 400  # Used for token calculations
MAX_WORDS_PER_REQUEST = 600000  # Max words per API call (~800K tokens)
MAX_TOKENS_PER_REQUEST = 800000  # Max tokens per API call
```

---

**Status:** ✅ Configuration updated, deduplication logic added

**Note:** Database still has 1000-word chunks until index is rebuilt.

