# Why "Chinese" (and similar broad queries) timed out — assessment

The query "Chinese" timed out after ~410s (limit 420s). Below are the existing mechanisms that were meant to avoid this, and why they did not help in this case.

---

## 1. Preprocessed deduplicated cache (`_try_use_preprocessed_file`)

**What it does:** For terms with many chunks, we can pre-build deduplicated text (sentence/phrase level) and store it in `data/deduplicated_terms/deduplicated_cache.json`. At query time, we look up the term (e.g. "Chinese") and, if found, replace the 100 raw chunks with pre-deduplicated content split into fewer chunks. That cuts LLM input size and work.

**Where it’s built:** `create_deduplicated_term_files()` in `lib/index_builder.py` (Step 6 of `build_index.py`). It runs only when you run the full index build locally. It only processes terms that have **>25 chunks** and are “meaningful” (identity terms, proper nouns, firm names). "Chinese" qualifies.

**Why it failed here:**

- **Cache never on Railway.** The cache lives under `data/deduplicated_terms/`. In `.gitignore`, `data/*` is ignored (except `identity_detection_v3.json`). So:
  - The cache is not in the repo and is not deployed with the app.
  - Railway never runs the full index build; it uses uploaded indices/vectordb. So the cache is never created on Railway.
- **Result:** For "Chinese", `_try_use_preprocessed_file` always finds no cache and returns `None`. We never use the optimized path; we always run with the full 100 chunks and runtime dedup.

**Fix (no caps):** Ensure the deduplicated cache is built as part of your release pipeline and deployed to Railway (e.g. build locally, then upload `data/deduplicated_terms/` or add an upload step/API for it). Document that step so it’s not skipped.

---

## 2. Runtime deduplication (`_deduplicate_and_combine_chunks`)

**What it does:** When no preprocessed file is used, we merge chunks and remove duplicate sentences and long phrases (7+ words) before sending to the LLM. This reduces tokens and repetition.

**Why it failed here:**

- **Low overlap for broad identity terms.** For "Chinese", the 100 chunks come from many different parts of the corpus (different regions, eras, topics). Sentence-level overlap between chunks is low, so dedup only trims a modest amount (e.g. 100 → 70–80 chunks).
- **Extra cost.** Dedup writes all chunks to a temp file, runs `_deduplicate_text_file`, then reads back. For 100 chunks that’s non-trivial I/O and CPU and adds time before we even call the LLM.
- **Still too many chunks.** We still send a large number of chunks (e.g. 70+) to the LLM/PeriodEngine, so total time stays high and we hit the timeout.

**Fix (no caps):** Rely more on the preprocessed cache (above) so we rarely need heavy runtime dedup for high-chunk terms. Optionally, for very high chunk counts, consider streaming or incremental dedup to avoid one big temp file.

---

## 3. Pre-limit (token-based) before deduplication

**What it does:** Before running dedup, we estimate tokens for the current chunk set. If we’re “way over” the allowed token budget, we trim the chunk list first to save work and stay within limits.

**Where:** `lib/query_engine.py` around 1390–1414: we only trim when  
`estimated_tokens_pre > effective_limit_pre * 1.3` (i.e. 30% over the limit).

**Why it failed here:**

- For 100 chunks, rough estimate is ~52k tokens; the effective limit is ~70k. So we’re under the limit and **below** the 1.3× threshold. The pre-limit never triggers; we never trim before dedup.
- So we still run full dedup on 100 chunks and then send a large set to the LLM.

**Fix (no caps):** Tighten the pre-limit so we trim earlier when we’re only slightly over (e.g. trigger when over 100% of the limit, or 1.1×, instead of 1.3×). That reduces work for queries like "Chinese" without hard caps on chunk count.

---

## 4. PeriodEngine / batched processing

**What it does:** For larger chunk counts (e.g. >50), we route to `PeriodEngine`, which processes by time period in batches so no single LLM call sees all chunks at once.

**Why it still timed out:**

- After dedup we still had on the order of 70+ chunks. PeriodEngine then runs multiple LLM calls (e.g. one or more per period). Each call has latency (model + network). With many periods/batches, **cumulative** time (fetch + dedup + all batches + review) exceeded 420s.
- So batching avoided a single huge request but did not bring total wall-clock time under the limit.

**Fix (no caps):** Reducing input size earlier (preprocessed cache + tighter pre-limit) means fewer chunks reach PeriodEngine and fewer batches, so total time can stay under the timeout. No need to cap chunk count if we shrink the working set by dedup and token limits.

---

## 5. Identity “finance-only” filtering

**What it does:** For identity queries we keep only chunks that contain strict banking/finance keywords (e.g. bank, finance, securities), so we drop off-topic passages.

**Why it didn’t save us here:**

- Many "Chinese" chunks in the corpus are already finance-related (banking, trade, etc.). So after filtering we still had a large number of chunks; the filter didn’t cut the set enough to avoid timeout.
- This step is still useful for quality; it’s just not sufficient alone for very broad identity terms.

---

## Summary

| Mechanism                    | Intended role              | Why it didn’t prevent timeout here                          |
|-----------------------------|----------------------------|-------------------------------------------------------------|
| Preprocessed dedup cache    | Shrink 100 chunks → fewer | Cache not built/deployed on Railway; never used             |
| Runtime dedup               | Shrink before LLM          | Low overlap for "Chinese"; still 70+ chunks; adds time      |
| Pre-limit (token-based)     | Trim before dedup          | 1.3× threshold too loose; pre-limit never triggered        |
| PeriodEngine batching       | Avoid one huge LLM call    | Many batches; total time still > 420s                      |
| Identity finance filtering  | Fewer, focused chunks     | Most "Chinese" chunks already finance; set still large      |

**Recommended direction (no caps):**

1. **Build and deploy the deduplicated cache** so high-chunk terms (e.g. "Chinese") use the preprocessed path on Railway.
2. **Tighten the pre-limit** (e.g. trigger at 1.0× or 1.1× of the token limit) so we trim earlier when over budget.
3. **Keep** runtime dedup, PeriodEngine, and identity filtering as-is; they help but weren’t enough because the cache wasn’t available and we didn’t trim soon enough.

These address the timeout by making existing optimizations (especially the cache and token limits) actually apply, rather than by adding new caps.

---

## Deploying the deduplicated cache to Railway

1. **Build locally** (creates `data/deduplicated_terms/deduplicated_cache.json`):
   ```bash
   python build_index.py
   ```
   Step 6 runs `create_deduplicated_term_files()` and writes the cache.

2. **Upload to Railway** via the admin endpoint:
   ```bash
   curl -X POST "https://YOUR-RAILWAY-URL/admin/upload-deduplicated-cache" \
     -F "file=@data/deduplicated_terms/deduplicated_cache.json"
   ```
   Or use the same pattern as your other uploads (e.g. PowerShell `Invoke-RestMethod` with `-Form`).

3. After upload, queries for high-chunk terms (e.g. "Chinese", "Jewish") will use the pre-deduplicated text when available, reducing LLM input and avoiding timeouts.

**Note:** `deduplicated_cache.json` can be large (~300+ MB). Use a long client timeout (e.g. `curl --max-time 600`). If the server rejects the body size, increase FastAPI's request body limit or use a chunked upload script.
