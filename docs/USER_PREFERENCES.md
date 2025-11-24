# User Preferences for Thunderclap AI

## Firm Phrase Matching (CRITICAL)

When querying firm phrases like "Rothschild Vienna", "Rothschild Paris", "Rothschild London", "Lazard London", "Lazard Paris", "Lazard New York", etc.:
- Use ONLY chunks indexed under that specific phrase
- Do NOT augment with later-period chunks that mention individual terms (e.g., "rothschild" OR "vienna" separately)
- Do NOT augment with crisis chunks using individual terms - use the firm phrase itself as anchor
- Firm phrases represent specific entities with specific operational periods - don't expand beyond their actual existence

**Rationale**: "Rothschild Vienna" is a specific entity that operated until 1938. Queries about it should not include content about "Rothschild London" or "Rothschild Paris" just because they share the word "Rothschild".

## Index Usage

- Trust the index - if "Rothschild Vienna" is indexed, use those chunks only
- Don't expand firm phrase queries with individual term unions
- Crisis augmentation should anchor on firm phrase when available, not individual terms

**Implementation**: 
- In `lib/query_engine.py`, crisis augmentation (lines 370-394) now prioritizes firm phrases over individual terms
- Later-period augmentation (lines 396-441) is disabled when firm phrases are matched

## Rate Limiting

- Respect 250k tokens/minute limit
- Use token-based rate limiting, not just request-based
- Track tokens used per minute and wait when approaching limits

**Implementation**:
- `MAX_TOKENS_PER_MINUTE = 250000` in `lib/config.py`
- `MAX_TOKENS_PER_REQUEST = 200000` (conservative limit)
- Token tracking and rate limiting in `QueryEngine._wait_for_token_rate_limit()`

## Deduplication

- Deduplicate and merge overlapping chunks
- Do NOT batch/combine chunks in deduplication function - that's handled by batching logic
- Keep chunks separate for proper processing

**Implementation**: 
- `_deduplicate_and_combine_chunks()` only deduplicates and merges overlaps
- Batching happens in `_generate_batched_narrative()` and PeriodEngine

## Review Iterations

- Limit to 5 iterations (not 20) to avoid excessive API calls
- Review system should detect issues but not loop excessively

**Implementation**: `MAX_REVIEW_ITERATIONS = 5` in `lib/config.py`

## Chunk Size

- 400-word chunks with 100-word overlap
- Smaller chunks improve precision and reduce duplication

**Implementation**: `CHUNK_SIZE = 400`, `CHUNK_OVERLAP = 100` in `lib/config.py`

## Summary

These preferences ensure queries stay focused on the specific entity queried and don't include unrelated content from other entities or time periods. The system should trust the index and use firm phrase matching precisely, without expanding to individual terms that might match unrelated entities.
