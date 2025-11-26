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

## Ideology Query Framework (Economic Systems)

For queries about economic systems (free markets, socialism, Marxism, command economies, mixed models), follow this checklist strictly:

### 1. System Definition
- Clearly define the economic system in theory.
- Distinguish between theoretical principles and real-world implementations.
- Identify where the system falls on the state vs market spectrum.

### 2. Sociological Perspective
- Describe impacts on social structures, class dynamics, labor relations, and social mobility.
- Tie social hierarchies or cultural norms to systemic features (e.g., dependency, inequality, incentives), rather than just historical narrative.
- Examine societal responses to economic policies and crises (strikes, protests, cohesion).

### 3. Banking & Financial Structures
- Explain the role of banking institutions, central banks, and commercial banks.
- Show how banking interacts with the system (state-controlled vs private, access to credit, regulation, liquidity).
- Explicitly connect banking structures to systemic outcomes and vulnerability to crises.

### 4. Financial Panics & Crises
- Identify systemic vulnerabilities (bank failures, credit crunches, housing busts, stock market crashes).
- Analyze how each system historically responded to crises, including social and economic consequences.
- Present events selectively, chronologically where helpful, but focus on illustrating system-level mechanisms and effects.
- Avoid assigning causes to ethnicity, religion, conspiracies, or moral character.

### 5. Evidence-Based Evaluation
- Prioritize empirical outcomes, measurable effects, or historical systemic performance.
- Avoid dense, multi-country narratives that don't illustrate systemic consequences.
- Link historical examples directly to system performance, banking, and social outcomes.

### 6. Trade-Offs & Systemic Analysis
- Explicitly compare strengths and weaknesses of each system across social, banking, and crisis dimensions.
- Discuss conditional scenarios under which each system performs well or poorly.
- Highlight trade-offs between efficiency, equity, stability, and societal impact.

### 7. Response Structure
1. System Definition & Theory
2. Sociological Impacts (class, social hierarchy, social mobility)
3. Banking & Financial Structures (bank types, access to credit, regulation)
4. Historical Financial Crises / Panics (chronological, selective, system-focused)
5. Trade-Offs & Interaction Effects (strengths, weaknesses, conditional performance)
6. Balanced Summary / Conditional Recommendations

### Strict Rules
- Avoid identity-based explanations (race, religion, ethnicity) for outcomes.
- Avoid ideological framing, moral judgments, or cherry-picked political anecdotes.
- Do not overwhelm with narrative history; prioritize causal links to systemic performance.
- Always distinguish between theoretical models and historical implementations.
- Present trade-offs and balanced analysis rather than declaring one system "better."

**Implementation**: 
- `lib/query_engine.py` - `_is_ideology_query()` detects economic system queries
- `lib/query_engine.py` - `_build_prompt_ideology()` contains the full framework
- `lib/economic_systems.py` - Contains definitions for all economic systems

## Summary

These preferences ensure queries stay focused on the specific entity queried and don't include unrelated content from other entities or time periods. The system should trust the index and use firm phrase matching precisely, without expanding to individual terms that might match unrelated entities. For economic system queries, the framework emphasizes systemic analysis, causal links, and balanced evaluation through sociology, banking, and financial panics lenses.
