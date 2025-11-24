# Index Rebuild Required
**Date:** 2025-01-21  
**Reason:** LGBTQ+ term grouping fix

## Changes Made

1. **Added LGBTQ+ terms to TERM_GROUPS** (`lib/index_builder.py`)
   - Merges variants: "gay"/"gays"/"homosexual"/"homosexuals"
   - Merges variants: "lgbt"/"lesbian"/"bisexual"/"queer"/"transgender"

2. **Added missing LGBTQ+ terms to identity_terms.py**
   - Added: 'homosexual', 'homosexuals', 'homosexuality', 'bisexual', 'bisexuals', 'queer', 'transgender', 'trans', 'lavender marriage', 'lavender marriages'

## Why Rebuild is Needed

The index was built **before** these terms were added to TERM_GROUPS. This means:
- "gay" and "gays" are currently separate indexed items
- "homosexual" and "homosexuals" are separate
- Queries for "gay" won't find chunks indexed under "homosexual"

After rebuild:
- All variants will be merged into unified term groups
- Queries will find comprehensive results

## How to Rebuild

```bash
python build_index.py
```

This will:
1. Re-index all documents
2. Apply TERM_GROUPS merging (including new LGBTQ+ groups)
3. Run identity detector
4. Create deduplicated cache
5. Take ~10-30 minutes depending on system

## Verify Fix

After rebuild, test queries:
- "Tell me about gay bankers"
- "Tell me about homosexual bankers"  
- "Tell me about lgbt bankers"

All should return comprehensive results covering all variants.

