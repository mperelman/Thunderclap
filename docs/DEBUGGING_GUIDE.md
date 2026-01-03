# Debugging Guide: Methodical Problem-Solving

## Philosophy

**Never assume. Always verify.**

When debugging, we follow a methodical approach:
1. **Observe** - What is actually happening?
2. **Hypothesize** - What could cause this?
3. **Test** - Create a test to verify the hypothesis
4. **Verify** - Does the fix actually work?
5. **Document** - Record what we learned

## The Problem-Solving Process

### Step 1: Observe and Document the Problem

**DO:**
- Document the exact behavior you see
- Note differences between environments (local vs Railway)
- Capture error messages, logs, or outputs
- Measure what you can (response length, chunk counts, timing)

**DON'T:**
- Jump to conclusions
- Assume you know the cause
- Claim you've "found the root cause" without verification

**Template:**
```
## Problem Report

**Observed Behavior:**
- [What actually happens]

**Expected Behavior:**
- [What should happen]

**Environment Differences:**
- Local: [details]
- Railway: [details]

**Measurements:**
- Response length: [X chars, Y paragraphs]
- Chunk count: [X chunks]
- Timing: [X seconds]
```

### Step 2: Form Hypotheses

**DO:**
- List multiple possible causes
- Rank by likelihood
- Consider each hypothesis independently

**DON'T:**
- Fixate on the first idea
- Ignore alternative explanations
- Assume the most obvious cause is correct

**Template:**
```
## Hypotheses (Ranked by Likelihood)

1. **Hypothesis 1:** [Description]
   - Why this could be the cause: [reasoning]
   - How to test: [test method]
   - Expected result if true: [what we'd see]

2. **Hypothesis 2:** [Description]
   - Why this could be the cause: [reasoning]
   - How to test: [test method]
   - Expected result if true: [what we'd see]

3. **Hypothesis 3:** [Description]
   - ...
```

### Step 3: Create Tests

**DO:**
- Write a test script that verifies the hypothesis
- Test in isolation if possible
- Compare local vs Railway behavior
- Make the test reproducible

**DON'T:**
- Skip testing
- Assume the fix works
- Test only in one environment

**Template:**
```python
"""Test: [Hypothesis description]

This test verifies: [What we're testing]
Expected result: [What should happen]
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup
# [Setup code]

# Test
# [Test code]

# Verify
# [Verification code]

print("✅ PASS" if test_passed else "❌ FAIL")
```

### Step 4: Verify the Fix

**DO:**
- Run the test script
- Verify it works in the environment where the problem occurred
- Check that the fix doesn't break other things
- Measure improvements (response length, quality, etc.)

**DON'T:**
- Claim it's fixed without testing
- Only test locally if the problem is on Railway
- Skip verification steps

**Verification Checklist:**
- [ ] Test script passes
- [ ] Fix works in problem environment (Railway/local)
- [ ] No regressions introduced
- [ ] Measurements show improvement
- [ ] Code review confirms fix is correct

### Step 5: Document the Solution

**DO:**
- Document the actual root cause (not assumptions)
- Record the verification steps taken
- Note any false leads or dead ends
- Include test scripts for future reference

**DON'T:**
- Document assumptions as facts
- Skip documenting false leads (they're valuable)
- Forget to include test scripts

**Template:**
```
## Solution Documentation

**Date:** [Date]
**Problem:** [Brief description]
**Root Cause:** [What actually caused it - verified, not assumed]
**Solution:** [What we changed]
**Verification:**
- Test script: [path to test]
- Test results: [pass/fail, measurements]
- Environment tested: [Railway/local/both]
- Response improvement: [before vs after]

**False Leads (What Didn't Work):**
1. [Hypothesis that was wrong]
   - Why it seemed right: [reasoning]
   - Why it was wrong: [what test showed]
   - Lesson learned: [insight]

**Key Insights:**
- [Important things we learned]
```

## Common Pitfalls to Avoid

### 1. The "I Found It!" Trap

**Symptom:** Immediately claiming you found the root cause after seeing code

**Reality:** You found a *possible* cause, not the *actual* cause

**Fix:** Always test before claiming

### 2. The "It Works Locally" Trap

**Symptom:** Fix works locally, assume it works everywhere

**Reality:** Local and Railway can have different environments

**Fix:** Test in the actual problem environment

### 3. The "One More Fix" Loop

**Symptom:** Keep making fixes without verifying previous ones

**Reality:** You're not addressing the actual problem

**Fix:** Verify each fix before moving to the next

### 4. The "Diagnostic Overload" Trap

**Symptom:** Adding more and more logging without using it

**Reality:** Logs are useless if you don't check them

**Fix:** Use diagnostics to answer specific questions

## Debugging Checklist

Before claiming a fix:

- [ ] I've observed the actual problem (not assumed what it is)
- [ ] I've formed a hypothesis about the cause
- [ ] I've created a test to verify the hypothesis
- [ ] The test confirms the hypothesis is correct
- [ ] I've implemented a fix
- [ ] I've verified the fix works in the problem environment
- [ ] I've measured the improvement (before/after)
- [ ] I've documented the solution with test results

## Example: Crédit Lyonnais Limited Response Issue

### Problem Report

**Observed Behavior:**
- Railway produces 4-paragraph responses for "Tell me about Crédit Lyonnais"
- Local produces 17-paragraph comprehensive responses
- Both use same code, same chunks (96 chunks)

**Expected Behavior:**
- Both should produce comprehensive responses

**Environment Differences:**
- Local: `use_async=True` (default), no async context
- Railway: `use_async=False` (server.py line 218), FastAPI async context

**Measurements:**
- Railway response: ~500 chars, 4 paragraphs
- Local response: 5,609 chars, 17 paragraphs
- Chunks: 96 chunks in both cases

### Hypotheses

1. **PeriodEngine not being called**
   - Test: Check logs for "[AUTO] Routing to PeriodEngine"
   - Status: ❌ Not the issue (PeriodEngine is being called)

2. **PeriodEngine failing silently**
   - Test: Check for "[WARN] PeriodEngine failed" messages
   - Status: ❌ Not the issue (no failures logged)

3. **Review being skipped**
   - Test: Check if `max_review_iter = 0` for >100 chunks
   - Status: ✅ Partially the issue (fixed, but not the only issue)

4. **use_async flag being ignored**
   - Test: Verify `process_iterative` checks `use_async` flag
   - Status: ✅ **ACTUAL ROOT CAUSE** - flag was ignored, always used async

### Solution

**Root Cause:** `process_iterative()` in `batch_processor_iterative.py` was ignoring `self.use_async` flag. It only checked if we're in an async context. Railway (FastAPI) runs in async context, so it always used `process_iterative_async` even when `use_async=False`.

**Solution:** Added check for `self.use_async` at the start of `process_iterative()`. If `False`, uses `process_iterative_sequential` directly.

**Verification:**
- Test script: `temp/verify_use_async_fix.py`
- Test results: ✅ PASS - `use_async=False` correctly uses sequential
- Environment tested: Local (verified fix works)
- Still need to verify: Railway (after deployment)

**False Leads:**
1. Review being skipped - This was a real issue, but fixing it didn't solve the problem
2. PeriodEngine not being called - PeriodEngine was being called, just using wrong method
3. Merge prompt differences - Both prompts were fine, issue was which one was used

**Key Insights:**
- Always verify flags are actually respected, not just set
- FastAPI's async context can interfere with sync/async decisions
- Test the actual code path, not just the code structure
