# Debugging Sessions Log

This file documents actual debugging sessions and their solutions.

## Format

Each session should include:
- **Problem:** What was the issue?
- **Observations:** What did we actually see?
- **Hypotheses:** What did we think might be the cause?
- **Tests:** How did we verify each hypothesis?
- **Solution:** What actually fixed it (verified, not assumed)?
- **False Leads:** What didn't work and why?

---

## Session: Crédit Lyonnais Limited Response (2025-01-22)

### Problem
Railway produces limited 4-paragraph responses for "Tell me about Crédit Lyonnais" while local produces comprehensive 17-paragraph responses.

### Observations
- Railway response: ~500 chars, 4 paragraphs, only covers 1901-1945
- Local response: 5,609 chars, 17 paragraphs, covers 1863-1960
- Both retrieve 96 chunks
- Both use same codebase
- Railway uses `use_async=False` (server.py line 218)
- Local uses `use_async=True` (default)

### Hypotheses Tested

1. **PeriodEngine not being called**
   - Test: Check logs for routing messages
   - Result: ❌ PeriodEngine IS being called

2. **Review being skipped for >100 chunks**
   - Test: Check `max_review_iter = 0` logic
   - Result: ✅ Partially true - fixed, but not the only issue

3. **Merge prompt differences**
   - Test: Compare `build_merge_prompt` vs async merge prompt
   - Result: ✅ Partially true - fixed, but not the only issue

4. **use_async flag being ignored**
   - Test: `temp/verify_use_async_fix.py` - verify flag is checked
   - Result: ✅ **ROOT CAUSE** - flag was ignored, always used async

### Solution

**Root Cause (VERIFIED):**
`process_iterative()` in `batch_processor_iterative.py` was ignoring `self.use_async` flag. It only checked if we're in an async context. Railway (FastAPI) runs in async context, so it always used `process_iterative_async` even when `use_async=False`.

**Fix:**
Added check for `self.use_async` at the start of `process_iterative()`. If `False`, uses `process_iterative_sequential` directly.

**Verification:**
- Test script: `temp/verify_use_async_fix.py`
- Test result: ✅ PASS - `use_async=False` correctly uses sequential
- Environment: Local (verified fix works)
- **Still pending:** Railway verification after deployment

**False Leads:**
1. Review being skipped - Real issue, but fixing it didn't solve the problem
2. Merge prompt differences - Both prompts were fine, issue was which one was used
3. PeriodEngine not being called - PeriodEngine was being called, just using wrong method

**Key Lessons:**
- Always verify flags are actually respected, not just set
- FastAPI's async context can interfere with sync/async decisions
- Test the actual code path, not just the code structure
- Multiple issues can exist simultaneously - fixing one doesn't mean problem is solved

**Files Changed:**
- `lib/batch_processor_iterative.py` - Added `use_async` check at start of `process_iterative()`
- `lib/query_engine.py` - Fixed review iteration logic, removed redundant re-ask logic
- `lib/prompts.py` - Added explicit ban on "provided information" phrases to `build_merge_prompt`

**Status:** Fix verified locally, pending Railway deployment verification

---

## Template for Future Sessions

```markdown
## Session: [Problem Name] ([Date])

### Problem
[Description]

### Observations
- [What we actually saw]

### Hypotheses Tested
1. **[Hypothesis]**
   - Test: [How we tested]
   - Result: [✅/❌ and what we learned]

### Solution
**Root Cause (VERIFIED):**
[What actually caused it - must be verified, not assumed]

**Fix:**
[What we changed]

**Verification:**
- Test script: [path]
- Test result: [pass/fail]
- Environment: [where tested]

**False Leads:**
[What didn't work and why]

**Key Lessons:**
[What we learned]

**Files Changed:**
[List of files]

**Status:** [Fixed/In Progress/Pending Verification]
```
