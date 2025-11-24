# Session Archive - January 21, 2025

## Changes Made

### 1. Removed 50-Chunk Cap
- Removed hardcoded limit that was capping chunks at 50 for literal identity queries
- Now processes all relevant chunks

### 2. Fixed Deduplication Logic
- Removed batching logic from `_deduplicate_and_combine_chunks()` 
- Now only deduplicates and merges overlapping chunks
- Batching happens separately in `_generate_batched_narrative()`

### 3. Token-Based Rate Limiting
- Added `MAX_TOKENS_PER_MINUTE = 250000` limit
- Reduced `MAX_TOKENS_PER_REQUEST` from 800k to 200k
- Added token tracking and rate limiting in `_wait_for_token_rate_limit()`
- All LLM calls now use `_call_llm_with_rate_limit()` wrapper

### 4. Reduced Review Iterations
- Changed `MAX_REVIEW_ITERATIONS` from 20 to 5

### 5. Fixed Firm Phrase Matching
- Fixed issue where "Rothschild Paris" and "Lazard Paris" weren't matching
- Now uses original raw tokens (before canonicalization) for phrase matching
- Handles cases where location names like "paris" canonicalize to "pari" but index has original form

### 6. Fixed Crisis Augmentation
- Now uses firm phrase as anchor (not individual terms) when firm phrase is matched
- Prevents unrelated entities from being included

### 7. Fixed Later-Period Augmentation
- Disabled later-period augmentation when firm phrases are matched
- Prevents expansion beyond entity's actual operational period

## Files Modified
- `lib/config.py` - Updated token limits and review iterations
- `lib/query_engine.py` - All fixes above
- `docs/USER_PREFERENCES.md` - Documented preferences

## Test Results
- ✅ "Rothschild Vienna" - Works correctly, stops at 1940
- ✅ "Rothschild Paris" - Now matches phrase correctly
- ✅ "Lazard Paris" - Now matches phrase correctly  
- ✅ "Rothschild London" - Works correctly
- ✅ Rate limiting - Respects 250k tokens/minute limit
- ✅ Deduplication - Properly merges overlapping chunks without over-batching


