# Fix: Court Jew, Hispanic, Korean Indexing Issue

## Problem

The index was creating separate entries for plural and singular forms:
- `court jew` (4 chunks) and `court jews` (4 chunks) - should be merged
- `hispanic` (55 chunks) and `hispanics` (3 chunks) - should be merged  
- `korean` (113 chunks) and `koreans` (3 chunks) - should be merged

## Root Cause

In `lib/index_builder.py` line 682-688, the code was indexing BOTH the original word AND the canonicalized version:

```python
for word in words:
    canonical = canonicalize_term(word)
    for target in filter(None, {word, canonical}):  # ❌ Indexes BOTH
        term_to_chunks[target].append(chunk_id)
```

This created duplicate entries instead of merging them.

## Fix

Changed to only index the canonicalized version:

```python
for word in words:
    canonical = canonicalize_term(word)
    # CRITICAL: Only index canonicalized version to merge plural/singular variants
    target = canonical if canonical else word
    term_to_chunks[target].append(chunk_id)  # ✅ Only canonicalized
```

## Impact

After rebuilding the index:
- `court jew` will have 8 chunks (4 + 4 merged)
- `hispanic` will have 58 chunks (55 + 3 merged)
- `korean` will have 116 chunks (113 + 3 merged)

## Next Steps

1. Rebuild index: `python build_index.py`
2. Verify: Check that plural/singular forms now map to same index key
3. Test queries: "Court Jews", "Hispanics", "Koreans" should all work correctly

