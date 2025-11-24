# Suggested Questions - Stricter Filtering Implemented

## Problem Identified

User feedback on Hohenemser narrative:
```
1. How did religious identity shape their opportunities? ❌ (docs don't discuss this)
2. What strategies did Ladenburg employ? ❌ (Ladenburg only mentioned in passing)
3. How did 1929 merger impact German economy? ❌ (docs only state merger happened)
```

**Issue**: LLM was suggesting questions about:
- Sociological analysis not present in docs
- Entities mentioned only tangentially (1-3 times)
- Causal/impact analysis when docs only state facts
- "How/Why" when docs only describe "what"

## Root Cause

The original prompt rule was too weak:
```
- Test: "Could I write multiple paragraphs answering this?" If yes → good question
```

LLM was interpreting this as "Could I write speculatively?" rather than "Could I write from what documents ACTUALLY say?"

## Solution Implemented

Updated prompts in 3 files:
1. `lib/prompts.py` (main prompt builder)
2. `lib/batch_processor_iterative.py` (large queries)
3. `lib/batch_processor_geographic.py` (event queries)

### New Rules (Much More Stringent)

```python
DO NOT SUGGEST QUESTIONS ABOUT:
✗ Sociological dynamics UNLESS documents explicitly discuss those dynamics
✗ Entities only mentioned 1-3 times in passing
✗ "How did X affect/impact Y?" when documents only state X occurred
  - BAD: "How did 1919 acquisition affect family?" (docs: acquisition happened)
  - GOOD: "What activities did family engage in after 1919?" (if docs describe)
✗ "Legacy" or "influence" questions when docs don't discuss legacy/influence
✗ "How" or "Why" questions when docs only describe "What" happened

CRITICAL CHECK for EACH question:
- Did the narrative I just wrote discuss the answer? If NO → DELETE
- Does narrative mention topic in only 1-2 sentences? If YES → DELETE

ONLY SUGGEST QUESTIONS ABOUT:
✓ Entities/families discussed across multiple paragraphs (5+ mentions)
✓ Topics where documents provide analysis, not just facts
✓ Time periods with rich detail
✓ Specific institutions/events covered in depth
```

### Key Addition

**"Did the narrative I just wrote discuss the answer? If NO → DELETE"**

This forces the LLM to:
1. Look back at what it actually wrote
2. Verify each question is answerable from that content
3. Delete questions about topics only briefly mentioned

## Test Results

**Before fix** (Hohenemser, 3 questions):
1. ❌ Religious identity impact (not discussed)
2. ❌ Ladenburg strategies (passing mention only)
3. ❌ Merger impact on economy (only stated event)

**After fix** (Hohenemser, 3 questions):
1. ✅ Hohenemser-Ladenburg connections (discussed: multiple marriages, board roles)
2. ✅ Joseph's role in Mannheim development (discussed: Leipzig Conference, Exchange founding)
3. ⚠️ Acquisition's effect on family (still problematic - asks impact when docs only state event)

## Remaining Issue

Question 3 still asks about "effects" when documents only state facts. The LLM may need:
- Even more explicit examples in prompt
- Or this is testing the limits of prompt engineering

## Next Steps

1. Monitor suggested questions across different query types
2. If pattern persists, add more explicit "BAD vs GOOD" examples
3. Consider post-processing filter to catch "How did X affect/impact" patterns

## Files Modified

- `lib/prompts.py` (lines 189-213)
- `lib/batch_processor_iterative.py` (lines 311-330)
- `lib/batch_processor_geographic.py` (lines 232-250)

All three now have consistent, strict filtering for suggested questions.



