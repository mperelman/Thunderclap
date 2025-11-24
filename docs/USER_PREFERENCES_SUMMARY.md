# User Preferences Summary

**Last Updated**: 2025-01-22

## Deduplication & TERM_GROUPS Preferences

### Deduplication Process

1. **Placement**: Deduplication happens AFTER TERM_GROUPS (not before, not as part of)
   - Rationale: TERM_GROUPS merges chunk IDs (fast), deduplication processes text (slow)
   - Location: Step 6 in `build_index.py`, after indices are built

2. **No Truncation**: Split large deduplicated texts into chunks instead of truncating
   - Large texts (>150K words) automatically split into multiple chunks
   - Each chunk uses maximum allowed size (150K words from `MAX_WORDS_PER_REQUEST`)
   - Number of chunks depends on text size (not hardcoded)

3. **Dynamic Sizing**: Use `MAX_WORDS_PER_REQUEST` from config (no hardcoding)
   - No hardcoded percentages (e.g., 80%)
   - Uses full LLM limit from config
   - Example: 490,443 words → 4 chunks (149,992, 150,000, 149,990, 39,588)

4. **Split by Sentences**: Preserve sentence boundaries for readability
   - Maintains coherence when splitting
   - Falls back to word-level splitting if needed

### TERM_GROUPS Behavior

1. **Build-Time Only**: TERM_GROUPS merges variants at index build time
   - Applied once during `build_index.py`
   - Queries use canonicalized terms and lookup index directly
   - No query-time TERM_GROUPS checks needed

2. **Purpose**: TERM_GROUPS merges chunk IDs (fast set operations)
   - All variants point to same chunks (e.g., "black" and "blacks" both have 1,503 chunks)
   - Applies to ALL 35 TERM_GROUPS, not just specific ones
   - Identity augmentation preserves TERM_GROUPS merges

3. **Query Handling**: 
   - Query engine canonicalizes terms (`canonicalize_term()`)
   - Looks up `term_to_chunks[keyword]` directly
   - Gets merged chunks automatically
   - `search_term()` method also canonicalizes before lookup

### Key Principles

1. **No Information Loss**: Split, don't truncate
2. **Dynamic Sizing**: Use config values, not hardcoded percentages
3. **Maximum Efficiency**: Use full LLM limits
4. **Separation of Concerns**: TERM_GROUPS (ID merging) vs Deduplication (text processing)
5. **Build-Time Processing**: TERM_GROUPS applied once, queries use results

## Code Organization Preferences

### File Organization
- Never create temporary files in main directory
- Use `temp/` folder for temporary files
- Use `tests/` folder for test files
- Archive old code in `archive/` directories

### Code Structure
- Prefer modular design over monolithic files
- Extract shared utilities to common modules
- Centralize configuration in `lib/config.py`
- Keep specialized engines in `lib/engines/`

## Efficiency Preferences

### Performance
- Use preprocessed cache when available
- Avoid redundant file operations
- Cache indices in memory
- Remove unused files (e.g., individual .txt files in deduplicated_terms/)

### Code Quality
- Extract duplicate code to shared utilities
- Keep functions focused on single responsibility
- Use centralized constants (stop words, identity terms, etc.)



