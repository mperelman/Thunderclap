# Indexing Fixes Complete

## Summary

Fixed three indexing issues that were causing incomplete search results:

1. **Plural/Singular Variants Not Merged** ✅ FIXED
2. **Underscore vs Space Versions Not Merged** ✅ FIXED  
3. **Identity Augmentation Happening After TERM_GROUPS Merge** ✅ FIXED

## Fixes Applied

### 1. Canonicalization Fix (`lib/index_builder.py` line 682-691)

**Problem:** Index was creating separate entries for plural and singular forms.

**Fix:** Changed to only index canonicalized version:
```python
# Before: Indexed both word AND canonical
for target in filter(None, {word, canonical}):  # ❌

# After: Only index canonicalized
target = canonical if canonical else word  # ✅
```

**Impact:**
- `hispanics` → `hispanic` (merged)
- `koreans` → `korean` (merged)
- All plural/singular variants now merge automatically

### 2. TERM_GROUPS Underscore Merging (`lib/index_builder.py` line 735-761)

**Problem:** Identity detector creates underscore versions (`court_jew`) but TERM_GROUPS uses spaces (`court jew`).

**Fix:** Added logic to merge underscore versions in TERM_GROUPS:
```python
# Check underscore versions of main term and variants
main_term_underscore = main_term.replace(' ', '_')
# Merge all chunks from space AND underscore versions
```

**Impact:**
- `court jew` + `court jews` + `court_jew` → all merged (721 chunks)
- `boston brahmin` + `boston_brahmin` → merged (125 chunks)
- `native american` + `native_american` → merged

### 3. Post-Augmentation Re-Merge (`build_index.py` line 117-138)

**Problem:** Identity augmentation happens AFTER TERM_GROUPS merge, so underscore versions added later weren't merged.

**Fix:** Added re-merge step after identity augmentation:
```python
# After identity augmentation, re-merge TERM_GROUPS
# to include underscore versions that were just added
```

**Impact:**
- Ensures all underscore versions from identity detector are merged with space versions
- Works for all multi-word TERM_GROUPS terms

## Verification Results

After rebuild:
- ✅ `court jew` / `court jews` / `court_jew`: All have 721 chunks (merged)
- ✅ `boston brahmin` / `boston_brahmin`: Both have 125 chunks (merged)
- ✅ `hispanic` / `hispanics`: Both map to `hispanic` (55 chunks) via canonicalization
- ✅ `korean` / `koreans`: Both map to `korean` (114 chunks) via canonicalization

## Status

✅ **All fixes applied and verified**
✅ **Index rebuilt successfully**
✅ **All variants now properly merged**

Queries for "Court Jews", "Hispanics", "Koreans", "Boston Brahmin" will now find all relevant chunks.

