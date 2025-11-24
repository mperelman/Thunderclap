# User Preferences: Deduplication & TERM_GROUPS

## Deduplication Preferences

### Placement
- **Deduplication happens AFTER TERM_GROUPS** (not before, not as part of)
- **Rationale**: TERM_GROUPS merges chunk IDs (fast), deduplication processes text (slow)
- **Location**: Step 6 in `build_index.py`, after indices are built

### Process
- **No truncation**: Split large deduplicated texts into chunks instead of truncating
- **Dynamic chunk sizing**: Use `MAX_WORDS_PER_REQUEST` from config (no hardcoding)
- **Split by sentences**: Preserve sentence boundaries for readability
- **Maximum efficiency**: Use full LLM limit (150,000 words per chunk)

### Implementation
- Large deduplicated texts (>150K words) are automatically split into multiple chunks
- Each chunk uses maximum allowed size (150K words)
- Number of chunks depends on text size (not hardcoded)
- Example: 490,443 words → 4 chunks (149,992, 150,000, 149,990, 39,588)

## TERM_GROUPS Preferences

### Purpose
- **Build-time only**: TERM_GROUPS merges variants at index build time
- **Query-time**: Queries use canonicalized terms and lookup index directly
- **No query-time TERM_GROUPS checks**: Already merged, no need to check again

### Behavior
- TERM_GROUPS merges chunk IDs (fast set operations)
- All variants point to same chunks (e.g., "black" and "blacks" both have 1,503 chunks)
- Applies to ALL 35 TERM_GROUPS, not just specific ones
- Identity augmentation preserves TERM_GROUPS merges

### Query Handling
- Query engine canonicalizes terms (`canonicalize_term()`)
- Looks up `term_to_chunks[keyword]` directly
- Gets merged chunks automatically
- `search_term()` method also canonicalizes before lookup

## Key Principles

1. **No information loss**: Split, don't truncate
2. **Dynamic sizing**: Use config values, not hardcoded percentages
3. **Maximum efficiency**: Use full LLM limits
4. **Separation of concerns**: TERM_GROUPS (ID merging) vs Deduplication (text processing)
5. **Build-time processing**: TERM_GROUPS applied once, queries use results



