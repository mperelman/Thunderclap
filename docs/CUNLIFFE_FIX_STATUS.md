# Cunliffe fix – why you see no difference

## What’s actually wrong

For the query **"Cunliffe"**, the app returns 9 unrelated passages. That only changes when the **code that runs on Railway** is the code that contains the fix.

**The code in this repo (the one you’re editing) already has the fix.** The app you’re hitting (https://web-production-c4223.up.railway.app) is almost certainly **not** running this repo’s code. So you keep seeing the old behavior no matter how many times we add or “fix” things here.

---

## The one fix (already in this repo)

**File:** `lib/query_engine.py`  
**Place:** Right before any LLM is called, after chunks are built (around lines 1434–1439).

**Logic:**

1. Filter chunks by the query term (e.g. only keep chunks that contain “Cunliffe”).
2. If **no** chunks contain the term → return the fallback message and **do not call the LLM**.
3. If some chunks contain the term → use only those chunks for the rest of the pipeline.

So for “Cunliffe”, if the 9 retrieved chunks don’t contain “Cunliffe”, the response is the short fallback message, not “Found 9 relevant passages”.

---

## Why you still see the old behavior

- **Railway runs whatever code it built from.**  
  “Redeploy” in Railway rebuilds the **same commit**; it does **not** pull new code from your machine or from GitHub until there is a **new commit** that Railway builds from.

- So if the commit that Railway last built **does not** include the early filter above, you will keep seeing the 15013‑character “Found 9 relevant passages” answer, no matter how many times you click Redeploy or how many sanitization layers we add in this repo.

---

## What you need to do (no more code changes needed here)

1. **Confirm this repo has the fix**  
   In `lib/query_engine.py` around line 1436 you should see something like:
   - `term_filtered = self._filter_chunks_by_question_terms(question, chunks)`
   - `if not term_filtered: ... return self._fallback_no_answer_message(question)`

2. **Get that code onto Railway**
   - Commit and push this repo to the **same GitHub repo and branch** that Railway is set to deploy from (often `main` or `master`).
   - Wait for Railway to **create a new deployment** from that new commit (do not rely on “Redeploy” on an old deployment).

3. **Confirm Railway is running the new build**
   - In Railway: check the **Deployments** tab and that the **latest** deployment is from the commit you just pushed.
   - Optionally open: https://web-production-c4223.up.railway.app/health  
     If the response includes `"sanitizer":"body-check-v2"`, that build includes the related checks. If it says `"missing"` or there is no `sanitizer` key, the running app is still an older build.

Until the **running** app on Railway is built from a commit that contains the early filter (and optionally the sanitizer), you will see **no** difference in behavior, no matter what we change in this repo.

---

## Summary

- **Root cause:** The response you see is produced by the code **currently running on Railway**, which is likely an older build.
- **Fix in this repo:** Already present (early filter in `lib/query_engine.py`; no further “sanitization” changes are required).
- **What’s left:** Deployment only — push this repo to the branch Railway deploys, and ensure Railway builds and runs that new commit. No further code changes here will change what you see until that happens.
