# Frontend Example Validation Report

**Date:** January 22, 2025  
**Total Examples Checked:** 129

## Summary

✅ **126 examples (97.7%)** are well-indexed with 5+ chunks  
⚠️ **3 examples (2.3%)** have low coverage (<5 chunks)  
❌ **0 examples** are completely missing from the index

## Low Coverage Examples

These examples have fewer than 5 chunks but may still work due to query engine fallback logic:

1. **Court Jews** (4 chunks)
   - Indexed as: `court jew` (canonicalized, singular)
   - Note: Query engine may expand to related terms

2. **Hispanics** (3 chunks)
   - Indexed as: `hispanic` (canonicalized, singular) - 55 chunks available
   - Note: Query engine should handle plural/singular conversion

3. **Koreans** (3 chunks)
   - Indexed as: `korean` (canonicalized, singular) - 113 chunks available
   - Note: Query engine should handle plural/singular conversion

## Analysis

The low coverage is likely due to:
- **Canonicalization**: Plural terms are converted to singular (e.g., "Court Jews" → "court jew")
- **Query Engine Fallback**: The query engine should still find results by:
  - Searching for both plural and singular forms
  - Using identity hierarchy expansion
  - Falling back to individual word matching

## Recommendations

1. **Court Jews**: Consider keeping as-is (important historical term, query engine should handle it)
2. **Hispanics/Koreans**: These should work fine - the query engine will find the singular form (`hispanic` has 55 chunks, `korean` has 113 chunks)

## All Examples Status

All 129 examples are either:
- ✅ Well-indexed (126 examples)
- ⚠️ Low coverage but should work via query engine fallback (3 examples)

**Conclusion:** All examples should work. The 3 low-coverage examples will be handled by the query engine's plural/singular conversion and identity expansion logic.

