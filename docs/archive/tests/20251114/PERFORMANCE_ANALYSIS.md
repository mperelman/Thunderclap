# Performance Analysis - Why Queries Take 2.5 Minutes

## Current Sequential Architecture (SLOW)

### For "Lehman" Query:
1. **Retrieved**: ~60-80 chunks
2. **Organized**: Into 3 periods (18th, 19th, 20th century)
3. **Processing**: All sequential

```
Period 1 (18th century):
  ├─ Batch 1 (20 chunks) → LLM call (25 sec)
  ├─ PAUSE 5 sec
  ├─ Batch 2 (20 chunks) → LLM call (25 sec)
  └─ PAUSE 5 sec (between periods)

Period 2 (19th century):
  ├─ Batch 1 (20 chunks) → LLM call (25 sec)
  ├─ PAUSE 5 sec
  ├─ Batch 2 (20 chunks) → LLM call (25 sec)
  └─ PAUSE 5 sec (between periods)

Period 3 (20th century):
  └─ Batch 1 (20 chunks) → LLM call (25 sec)

Final merge: 1 LLM call (30 sec)

TOTAL: ~150 seconds = 2.5 minutes
```

## Bottlenecks Identified

1. **Sequential periods**: Process one period at a time
   - Line 72-88 in `batch_processor_iterative.py`
   - Could run Period 1, 2, 3 in parallel!

2. **Sequential batches within period**: Process one batch at a time
   - Line 153-167 in `batch_processor_iterative.py`
   - Could run Batch 1 and 2 in parallel!

3. **Unnecessary pauses**: 5-second sleep between each batch
   - Originally to respect rate limits
   - But Gemini allows 15 RPM = can do 10-12 concurrent!

4. **Synchronous API calls**: No async/await
   - All LLM calls use blocking `client.generate_content()`
   - Should use async API calls with concurrency control

## Optimization Strategy

### API Rate Limits (Gemini 2.0 Flash):
- 15 RPM (requests per minute)
- 1M TPM (tokens per minute) 
- 200 RPD (requests per day)

**Current**: 0 concurrent requests (sequential)
**Optimal**: 10-12 concurrent requests (stay under 15 RPM)

### Speedup Calculation:

**Sequential** (current):
- 6 batch calls × 25 sec = 150 sec
- 5 pauses × 5 sec = 25 sec
- 1 merge call × 30 sec = 30 sec
- **TOTAL: 205 seconds (~3.5 min)**

**Parallel** (with 10 concurrent):
- All 6 batches in parallel (limited by RPM):
  - Batch 1-10: 25 sec (concurrent)
  - Batch 11-15: Not applicable here (only 6 batches)
- 1 merge call: 30 sec
- **TOTAL: 55 seconds (~1 min)**

### Expected Speedup: **3-4x faster!**

## Implementation Plan

### Phase 1: Async API Calls (Easy - 30 min)
```python
import asyncio
import google.generativeai as genai

# Instead of:
response = client.generate_content(prompt)

# Use:
response = await client.generate_content_async(prompt)
```

### Phase 2: Concurrent Batching (Medium - 1 hour)
```python
# Use asyncio.Semaphore to limit concurrent requests
semaphore = asyncio.Semaphore(10)  # Max 10 concurrent

async def process_batch_with_limit(batch):
    async with semaphore:
        return await llm.call_api_async(prompt)

# Process all batches concurrently
results = await asyncio.gather(*[
    process_batch_with_limit(batch) 
    for batch in batches
])
```

### Phase 3: Remove Unnecessary Pauses (Easy - 5 min)
```python
# DELETE:
time.sleep(5)  # Not needed with semaphore rate limiting

# Semaphore handles rate limiting automatically
```

### Phase 4: Parallel Period Processing (Medium - 1 hour)
```python
# Instead of sequential:
for period in periods:
    narrative = process_period(period)

# Use concurrent:
period_tasks = [
    process_period_async(period) 
    for period in periods
]
results = await asyncio.gather(*period_tasks)
```

## Files to Modify

1. **`lib/llm.py`**:
   - Add `async def call_api_async()`
   - Use `generate_content_async()`

2. **`lib/batch_processor_iterative.py`**:
   - Convert to async: `async def process_iterative()`
   - Add semaphore for rate limiting
   - Remove `time.sleep()` calls
   - Use `asyncio.gather()` for concurrent processing

3. **`lib/query_engine.py`**:
   - Update to call async methods with `asyncio.run()`

## Expected Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Query time | 2.5 min | 45-60 sec | **3-4x faster** |
| API calls | 7 sequential | 6 parallel + 1 merge | Same total |
| RPM usage | 2-3 RPM | 10-12 RPM | **5x better utilization** |
| Pauses | 6 × 5 sec = 30 sec | 0 sec | **30 sec saved** |

## Risks & Mitigation

### Risk 1: Hit 15 RPM limit
- **Mitigation**: Use `Semaphore(10)` to stay under limit
- Monitor and adjust if needed

### Risk 2: Hit 200 RPD limit faster
- **Current**: ~200 chunks/day = ~10 queries
- **After**: Same API calls, just faster
- **Impact**: None (same total requests)

### Risk 3: Async complexity
- **Mitigation**: Keep sync versions as fallback
- Use `asyncio.run()` wrapper for compatibility

## Next Steps

Want me to implement this? It will:
1. ✅ Make queries 3-4x faster (2.5 min → 45 sec)
2. ✅ Better utilize API rate limits
3. ✅ Keep same total API calls (no extra cost)
4. ✅ Maintain all existing functionality


