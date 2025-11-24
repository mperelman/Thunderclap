# LGBTQ+ Term Grouping Fix
**Date:** 2025-01-21  
**Issue:** Missing information for LGBTQ+ queries (gay/lgbt/homosexual)

## Problem Identified

User reported that queries about LGBTQ+ bankers were missing a lot of information. Investigation revealed:

1. **LGBTQ+ terms were NOT in TERM_GROUPS**
   - Variants like "gay"/"gays", "homosexual"/"homosexuals" were indexed separately
   - Queries for "gay" wouldn't find chunks indexed under "gays" or "homosexual"
   - No term grouping to merge these variants

2. **Search relies on TERM_GROUPS for variant merging**
   - `search_term()` uses `canonicalize_term()` to match TERM_GROUPS
   - Without TERM_GROUPS entry, variants aren't merged
   - Results are incomplete

## Solution

Added LGBTQ+ terms to TERM_GROUPS in `lib/index_builder.py`:

```python
# LGBTQ+ identities (keyword-based, not individual tagging - see docs/archive/LGBT_LATINO_APPROACH.md)
'gay': ['gay', 'gays', 'homosexual', 'homosexuals', 'homosexuality'],
'lgbt': ['lgbt', 'lgbtq', 'lgbtq+', 'lesbian', 'lesbians', 'bisexual', 'bisexuals', 
         'queer', 'transgender', 'trans', 'lavender marriage', 'lavender marriages'],
```

## Why This Approach

According to `docs/archive/LGBT_LATINO_APPROACH.md`:
- **LGBTQ+ is keyword-search only** (not individual tagging)
- This is correct because LGBTQ+ identity is about **historical context** (lavender marriages, AIDS crisis, homophobia)
- We want chunks that **discuss** LGBTQ+ topics, not chunks about individuals who happen to be LGBTQ+
- Tagging individuals would incorrectly include ALL chunks about them (e.g., all Drexel chunks, not just lavender marriage ones)

## Next Steps

**REBUILD INDEX** to apply the fix:

```bash
python build_index.py
```

This will:
1. Re-index all terms with LGBTQ+ variants properly grouped
2. Merge "gay"/"gays"/"homosexual"/"homosexuals" into same chunk set
3. Merge "lgbt"/"lesbian"/"bisexual" variants into same chunk set
4. Enable comprehensive LGBTQ+ searches

## Expected Behavior After Rebuild

### Before Fix
- Query "gay bankers" → Only finds chunks with exact word "gay"
- Query "homosexual bankers" → Only finds chunks with exact word "homosexual"
- Missing chunks that use variants ("gays", "homosexuals", "homosexuality")

### After Fix
- Query "gay bankers" → Finds ALL chunks with "gay", "gays", "homosexual", "homosexuals", "homosexuality"
- Query "lgbt bankers" → Finds ALL chunks with "lgbt", "lesbian", "bisexual", "queer", "transgender", "lavender marriage"
- Comprehensive coverage of LGBTQ+ content

## Related Files

- `lib/index_builder.py` - TERM_GROUPS definition (lines 91-92)
- `lib/query_engine.py` - `search_term()` uses TERM_GROUPS via `canonicalize_term()`
- `docs/archive/LGBT_LATINO_APPROACH.md` - Explains why keyword-only approach is correct

