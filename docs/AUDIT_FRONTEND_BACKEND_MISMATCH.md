# Audit: Frontend-Backend Mismatch Issue (Jan 22, 2025)

## Executive Summary

**Root Cause**: Frontend (GitHub Pages) and backend (Railway) got out of sync after backend was restored to an older synchronous version, while frontend remained on async polling pattern.

**Fix**: Restored full async background job processing pattern from commit `a3ae9ab` to match frontend expectations.

**Impact**: 18+ failed fix attempts over several hours before root cause was identified and fixed.

---

## Timeline of Events

### 1. Original Working State (Nov 24, 2025 - commit `a3ae9ab`)

**Both frontend and backend used async polling pattern:**

- **Frontend (`index.html`)**: 
  - POST `/query` → receives `{job_id, status, message}`
  - Polls GET `/query/{job_id}` for status
  - Expects `{status, answer}` in status response

- **Backend (`server.py`)**:
  - POST `/query` → returns `QueryJobResponse` with `job_id` immediately
  - Background task processes query asynchronously
  - GET `/query/{job_id}` → returns `QueryStatusResponse` with status and answer
  - Uses `JOB_STORE` dict to track job status

**Why async?** To avoid Railway proxy timeout (30-60s) for long-running queries.

---

### 2. The Break (Jan 22, 2025 - commit `4a500dc`)

**What happened:**
- User updated ideology query framework and preferences
- Backend was "restored" to commit `4a500dc` (synchronous version)
- **Frontend on GitHub Pages was NOT updated** - still had async version from `a3ae9ab`

**Result**: Mismatch
- Frontend expects: `{job_id}` → poll `/query/{job_id}` → get `{status, answer}`
- Backend provides: Direct `{answer}` response (synchronous)

---

### 3. Failed Fix Attempts (Jan 22, 2025 - 18+ commits)

**Pattern of failures:**
1. **Partial fixes** - Added status endpoint but kept synchronous processing
2. **Field name mismatches** - Added `request_id` but frontend expected `job_id`
3. **Response format issues** - Frontend couldn't read headers, needed JSON body
4. **Missing answer storage** - Status endpoint couldn't return answer

**Key failed commits:**
- `e6d5693`: Added `/query/{request_id}` but no background processing
- `448fe61`: Added `request_id` to response body
- `427cc94`: Returned 'complete' for undefined `request_id` (hack)
- `9a83ddc`: Tried to fix `.match()` error on undefined
- `14e8d72`: Restored "working" version but it was synchronous
- `de349d8`: Added `ANSWER_STORE` but still synchronous processing

**Why they failed:**
- All were partial fixes trying to make synchronous backend work with async frontend
- Never addressed root cause: backend needs to process queries in background

---

### 4. The Fix (Jan 22, 2025 - commit `06d18bd`)

**What was done:**
- Restored full async pattern from commit `a3ae9ab`
- POST `/query` → returns `QueryJobResponse` with `job_id` immediately
- Background task processes query using `BackgroundTasks`
- GET `/query/{job_id}` → returns `QueryStatusResponse` with status and answer
- Uses `JOB_STORE` to track job state

**Why it worked:**
- Backend now matches frontend expectations exactly
- Async processing avoids Railway timeout
- Proper job tracking allows frontend polling to work

---

## Technical Details

### Frontend Expectations (from `index.html` on GitHub Pages)

```javascript
// 1. POST /query
POST /query
Body: {question: "...", max_length: 15000}
Expected Response: {job_id: "...", status: "pending", message: "..."}

// 2. Poll GET /query/{job_id}
GET /query/{job_id}
Expected Response: {job_id: "...", status: "complete|processing|error", answer: "...", elapsed: ...}
```

### Backend Before Fix (Synchronous)

```python
@app.post("/query")
async def query(...):
    # Process query synchronously (blocks for 40-60s)
    answer = qe.query(question, use_llm=True)
    return QueryResponse(answer=answer, request_id=..., job_id=...)
```

**Problems:**
- Returns answer directly (frontend expects `job_id` first)
- No background processing
- Blocks Railway proxy (may timeout)
- Frontend polls `/query/undefined` because no `job_id` in response

### Backend After Fix (Async)

```python
@app.post("/query", response_model=QueryJobResponse)
async def query(..., background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    JOB_STORE[job_id] = {"status": "pending", ...}
    background_tasks.add_task(process_query_job, job_id, ...)
    return QueryJobResponse(job_id=job_id, status="pending", ...)

@app.get("/query/{job_id}", response_model=QueryStatusResponse)
async def get_query_status(job_id: str):
    job = JOB_STORE[job_id]
    return QueryStatusResponse(
        job_id=job_id,
        status=job.get("status"),
        answer=job.get("answer"),
        elapsed=...
    )
```

**Why it works:**
- Returns `job_id` immediately (matches frontend)
- Background task processes query (avoids timeout)
- Status endpoint returns answer when ready (matches frontend polling)

---

## Lessons Learned

### 1. **Deployment Synchronization**
- **Problem**: Frontend (GitHub Pages) and backend (Railway) can get out of sync
- **Solution**: Always verify both are on compatible versions before "restoring" code

### 2. **Root Cause Analysis**
- **Problem**: 18+ commits trying partial fixes without identifying root cause
- **Solution**: Should have checked what frontend actually expected vs what backend provided

### 3. **Architecture Understanding**
- **Problem**: Didn't realize async pattern was intentional (to avoid Railway timeout)
- **Solution**: Understand why architecture decisions were made before reverting

### 4. **Frontend Code Visibility**
- **Problem**: Frontend code on GitHub Pages not visible in this repo during debugging
- **Solution**: Check deployed frontend or ask user for frontend code when debugging API mismatches

---

## Prevention

### Checklist Before "Restoring" Code:

1. ✅ Check if frontend was updated separately (GitHub Pages, CDN, etc.)
2. ✅ Verify frontend expectations (API contract)
3. ✅ Test with actual frontend, not just backend unit tests
4. ✅ Understand why original architecture was chosen (async for timeout avoidance)
5. ✅ If restoring, restore BOTH frontend and backend together

### When Frontend-Backend Mismatch Suspected:

1. **Check deployed frontend** - What does it actually expect?
2. **Check git history** - When was frontend last updated?
3. **Compare API contracts** - What fields/endpoints does frontend use?
4. **Test end-to-end** - Don't just test backend in isolation

---

## Files Changed

### Final Fix (commit `06d18bd`):
- `server.py`: Restored async background job processing pattern

### Key Commits:
- `a3ae9ab` (Nov 24): Original async implementation
- `4a500dc` (Jan 22): Backend restored to sync (broke it)
- `06d18bd` (Jan 22): Fixed by restoring async pattern

---

## Status

✅ **RESOLVED** - Backend now matches frontend async polling pattern.

**Verification:**
- Frontend receives `job_id` immediately
- Frontend polls `/query/{job_id}` successfully
- Frontend receives `answer` when query completes
- No more `.match()` errors or `undefined` request IDs

