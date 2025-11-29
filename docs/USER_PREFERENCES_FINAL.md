# User Preferences - Final Version
## Saved: 2025-01-22

This document memorializes the user's narrative preferences for Thunderclap AI.

## Source
These preferences are extracted from `.cursorrules` and represent the complete set of rules for generating historical narratives.

## Key Preferences

### 0. RELEVANCE ABOVE ALL (TOP PRIORITY)
- ONLY include information that DIRECTLY involves the query subject
- Filter out unrelated entities that appear in the same document chunk
- Every sentence must directly involve the subject

### 1. ACCURACY - NEVER FABRICATE (SECOND PRIORITY)
- ONLY state what documents EXPLICITLY say
- NO inferences, assumptions, or combinations
- Better to be incomplete than inaccurate

### 2. Subject Must Be Active in EVERY Sentence
- Subject should be the actor, not the object

### 3. Only Include Directly Relevant Information
- Test each sentence: "Does this involve the query subject?"

### 4. No Platitudes or Flowery Language
- Avoid phrases like "dynamic nature", "testament to", "journey", "transformative era"

### 5. Thunderclap Framework (CRITICAL)
- View history through SOCIOLOGICAL + PANIC lenses
- Analyze identity in EVERY time period
- Cover ALL Panics in ALL time periods
- Maintain sociological analysis THROUGHOUT

### 6. Naming Conventions
- INSTITUTIONS: Use italics (*Hope*, *Lehman*)
- PEOPLE: Regular text
- NEVER use "& Co." or "& Company"
- Be CONSISTENT with abbreviations

### 7. Clear Chronological Organization
- Organize STRICTLY by time periods
- Move forward in time - NEVER jump backwards
- Cover ALL time periods documents mention

### 8. Writing Style: Bernanke + Maya Angelou
- Mix analytical rigor with humanizing details
- Show people as human beings navigating constraints

### 9. Provide Related Questions at End
- 3-5 follow-up questions
- Questions should be about topics with enough content for substantive narratives

## System Configuration
- 2,039 indexed chunks (updated from source documents)
- 31,954 terms indexed
- 500-word chunks with 100-word overlap
- Term grouping enabled (jew/jews/jewish, etc. return same results)

## See Also
- `.cursorrules` - Full detailed preferences
- `lib/prompts.py` - LLM prompt templates implementing these preferences

