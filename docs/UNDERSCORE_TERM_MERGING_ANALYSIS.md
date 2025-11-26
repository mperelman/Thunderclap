# Underscore Term Merging Analysis

## Problem

The identity detector creates underscore-separated terms (e.g., `court_jew`, `boston_brahmin`) while the word-by-word indexer creates space-separated terms (e.g., `court jew`, `boston brahmin`). These were not being merged, causing incomplete search results.

## Affected Terms

### Multi-word TERM_GROUPS with underscore versions:

1. **court jew** (CRITICAL)
   - Space version: 4 chunks
   - Underscore version: 721 chunks
   - **Missing: 721 chunks (99.4% of data!)**

2. **boston brahmin** (SIGNIFICANT)
   - Space version: 101 chunks
   - Underscore version: 90 chunks
   - **Missing: 90 chunks (47% of data)**

3. **native american** (MINOR)
   - Space version: 36 chunks
   - Underscore version: 2 chunks
   - **Missing: 2 chunks (5% of data)**

## Other Identity-Related Underscore Terms

These underscore terms exist in the index but may not be in TERM_GROUPS:
- `greek_orthodox` (44 chunks) - matches "greek orthodox" in TERM_GROUPS
- `new_christian` (201 chunks) - not in TERM_GROUPS
- `protected_jew` (35 chunks) - not in TERM_GROUPS
- `latin_american` (85 chunks) - not in TERM_GROUPS
- `mint_jew` (21 chunks) - not in TERM_GROUPS
- `state_jew` (9 chunks) - not in TERM_GROUPS

## Fix Applied

The fix in `lib/index_builder.py` (lines 735-750) now:
1. Checks for underscore versions of main TERM_GROUPS terms
2. Checks for underscore versions of all variants
3. Merges all chunks from space and underscore versions
4. Stores both space and underscore versions pointing to merged chunks

## Impact

After rebuilding the index:
- `court jew` will have 725 chunks (4 + 721 merged) ✅
- `boston brahmin` will have 191 chunks (101 + 90 merged) ✅
- `native american` will have 38 chunks (36 + 2 merged) ✅

## Remaining Issues

Some underscore terms are not in TERM_GROUPS and won't be automatically merged:
- `new_christian` (201 chunks) - might need to be added to TERM_GROUPS
- `protected_jew` (35 chunks) - might need to be added to TERM_GROUPS
- `greek_orthodox` (44 chunks) - already in TERM_GROUPS as variant, should merge

These can be addressed by:
1. Adding them to TERM_GROUPS if they're important identity categories
2. Or manually checking if they have space equivalents that should be merged

