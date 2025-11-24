# Query Timeout Fixes
**Date:** 2025-01-21  
**Issue:** Queries timing out with "Connection lost" errors

## Problem Analysis

Users were experiencing timeout errors with the message:
> "⚠️ Connection lost. The query might be taking too long (large queries take 30-90 seconds)."

### Root Causes Identified

1. **Server Keep-Alive Timeout Too Short**
   - `timeout_keep_alive=360` (6 minutes) was shorter than `QUERY_TIMEOUT_SECONDS=420` (7 minutes)
   - This caused the connection to drop before queries could complete

2. **Blocking Call in Async Endpoint**
   - Server endpoint is `async def query()` but was calling `qe.query()` synchronously
   - This blocked the async event loop, potentially causing connection issues

3. **No Timeout Wrapper**
   - No explicit timeout handling at the server level
   - Queries could run indefinitely until hitting system limits

## Fixes Applied

### 1. Increased Server Keep-Alive Timeout ✅
**File:** `server.py` (line 189)

**Before:**
```python
uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=360)
```

**After:**
```python
# Increase timeout for long-running queries (8 minutes to exceed frontend timeout of 7 minutes)
# timeout_keep_alive must exceed QUERY_TIMEOUT_SECONDS (420s = 7min) to prevent connection drops
uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=480)
```

**Impact:** Connection now stays alive for 8 minutes, exceeding both query timeout (7 min) and frontend timeout (7 min).

### 2. Proper Async Handling ✅
**File:** `server.py` (lines 139-158)

**Before:**
```python
# Process query (uses sequential processing to avoid event loop conflicts)
query_start = time.time()
answer = qe.query(req.question, use_llm=True)
```

**After:**
```python
# Process query (uses sequential processing to avoid event loop conflicts)
# Run blocking query in executor to avoid blocking async event loop
# Add timeout wrapper to ensure we don't exceed QUERY_TIMEOUT_SECONDS
import asyncio
loop = asyncio.get_event_loop()
query_start = time.time()

# Wrap query in timeout to prevent exceeding server timeout
try:
    answer = await asyncio.wait_for(
        loop.run_in_executor(None, lambda: qe.query(req.question, use_llm=True)),
        timeout=QUERY_TIMEOUT_SECONDS - 10  # Leave 10s buffer for cleanup
    )
except asyncio.TimeoutError:
    query_time = time.time() - query_start
    trace_event(request_id, "query_timeout", duration=query_time)
    raise HTTPException(
        status_code=504,
        detail=f"Query timed out after {query_time:.1f}s (limit: {QUERY_TIMEOUT_SECONDS}s). Request ID: {request_id}"
    )
```

**Impact:** 
- Blocking query now runs in executor thread, not blocking event loop
- Explicit timeout wrapper catches timeouts early
- Better error messages with Request ID for debugging

## Configuration Summary

| Component | Timeout Value | Notes |
|-----------|--------------|-------|
| Frontend | 420s (7 min) | Client-side abort timeout |
| Server Keep-Alive | 480s (8 min) | **Fixed:** Now exceeds query timeout |
| Query Timeout | 420s (7 min) | Maximum query processing time |
| Server Timeout Wrapper | 410s (6m 50s) | Leaves 10s buffer for cleanup |

## Testing Recommendations

1. **Test Normal Queries**
   - Simple queries should complete in < 30 seconds
   - No timeout errors expected

2. **Test Large Queries**
   - Broad identity queries (e.g., "Tell me about black bankers")
   - Should complete in 30-90 seconds
   - No "Connection lost" errors

3. **Test Very Large Queries**
   - Complex multi-period queries
   - Should complete in 2-5 minutes
   - Should timeout gracefully at 7 minutes if too large

4. **Monitor Server Logs**
   - Check for `[TRACE] query_timeout` events
   - Verify Request IDs are logged for debugging
   - Check `/status` endpoint for recent requests

## Expected Behavior

### Before Fixes
- ❌ Connection drops after 6 minutes even if query is still processing
- ❌ "Connection lost" error with no clear timeout reason
- ❌ Event loop blocked by synchronous query call

### After Fixes
- ✅ Connection stays alive for 8 minutes (exceeds query timeout)
- ✅ Explicit timeout errors with Request ID for debugging
- ✅ Non-blocking async execution
- ✅ Graceful timeout handling with proper error messages

## Related Files

- `server.py` - Server timeout configuration and async handling
- `lib/config.py` - `QUERY_TIMEOUT_SECONDS` configuration
- `lib/query_engine.py` - Query processing with timeout checks
- `frontend.html` - Client-side timeout handling

## Notes

- The query engine already has internal timeout checks in `_review_and_fix_answer()`
- Rate limiting pauses (4-12 seconds) between LLM API calls are expected and necessary
- Very large queries may still take 2-5 minutes - this is normal for complex queries
- If queries consistently timeout, consider:
  - Simplifying the query
  - Breaking into smaller sub-queries
  - Checking server logs for bottlenecks

