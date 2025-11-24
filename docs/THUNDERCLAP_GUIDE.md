# Thunderclap AI - Complete Guide

This guide explains the Thunderclap framework embedded in the codebase and the AI's narrative preferences.

## Critical Rules (Priority Order)

### 0. RELEVANCE ABOVE ALL
- ONLY include information that DIRECTLY involves the query subject
- Test for EVERY sentence: "Does this involve [query subject]?" If NO → DELETE IT
- Don't include tangential facts just because they're in the same document chunk
- See: `lib/prompts.py` - `CRITICAL_RELEVANCE_AND_ACCURACY`

### 1. ACCURACY - NEVER FABRICATE
- ONLY state what documents EXPLICITLY say
- Do NOT connect separate entities unless document explicitly connects them
- Do NOT mention panics/laws unless explicitly linked to the subject
- Better to be incomplete than inaccurate
- See: `lib/prompts.py` - `CRITICAL_RELEVANCE_AND_ACCURACY`

## Thunderclap Framework (Embedded in Code)

The system analyzes all narratives through **SOCIOLOGICAL + PANIC lenses**.

### Location in Code:
- **Primary**: `lib/prompts.py` - All prompt templates
- **Secondary**: `.cursorrules` - AI assistant instructions
- **Data**: `lib/identitys.py` - identity definitions (single source of truth)

### Key Components:

#### 1. SOCIOLOGY - identitys & Minority Middlemen
**See:** `lib/prompts.py` - `THUNDERCLAP_SOCIOLOGY_FRAMEWORK`

**Core Concept:**
- Banking dominated by **small intermarried elite families** (identitys), NOT entire populations
- Examples loaded dynamically from `lib/identitys.py`

**Key Patterns:**
- **identityS**: Small intermarried elite families
- **MINORITY MIDDLEMEN**: Exclusion from land/politics/industry → channeled into finance
- **KINLINKS** (FUNDAMENTAL): Most identitys kinlinked extensively outside their grouping
- **CASTE**: Within-group hierarchies (Kohanim among Jews, Brahmin among Hindus)
- **CONVERSIONS**: How conversions affected access

**For Details:** See `docs/identity_REFERENCE.md` - comprehensive table with all families

#### 2. PANICS - Organizing Framework
**See:** `lib/prompts.py` - `THUNDERCLAP_PANIC_FRAMEWORK`

- Cover EVERY Panic documents mention (1763, 1825, 1837, 1873, 1893, 1907, 1929, etc.)
- ONLY include panics if documents explicitly link them to the subject
- For each: What happened? How did identity shape outcome?

#### 3. NETWORKS & REGULATIONS
**See:** `lib/prompts.py` - `THUNDERCLAP_NETWORKS_REGULATIONS`

- Show specific marriages/partnerships and what they enabled
- How did regulations change access to opportunities?
- Connect to identity if documents support it

## Narrative Structure (Embedded in Code)

**See:** `lib/prompts.py` - `NARRATIVE_STRUCTURE_RULES`

### Key Requirements:

1. **Subject Active**: "*Lehman* merged with Goldman" (NOT "Goldman merged with *Lehman*")

2. **Strict Chronology**: 
   - Organize by time periods (1770s-1790s → 1800-1815 → 1820s-1840s)
   - NEVER jump backwards (e.g., 1957 → 1783 is WRONG)
   - Cover ALL time periods documents mention - don't skip centuries

3. **Connected Narrative**:
   - Use transitions between paragraphs
   - Show how earlier events shaped later ones
   - Build a narrative arc, not disconnected statements

4. **Comprehensive Coverage**:
   - Cover ALL time periods, families, aspects mentioned
   - Include periods of decline/transition
   - Don't provide sparse, scattered statements

5. **Short Paragraphs**: 3-4 sentences max, one topic per paragraph

## Naming Conventions (Embedded in Code)

**See:** `lib/prompts.py` - `NAMING_CONVENTIONS`

- **Institutions**: *Hope*, *Lehman*, *Morgan* (italics)
- **People**: Henry Hope, Henry Lehman (regular text)
- **NEVER** use "& Co." or "& Company"
- **Consistent**: "WWI" and "WWII" (not "World War I" then "WWII")

## Writing Style (Embedded in Code)

**See:** `lib/prompts.py` - `WRITING_STYLE`

- **Mix Bernanke** (analytical rigor) + **Maya Angelou** (humanizing details)
- Include events that humanize people ("fled to London", "worked from home as widow")
- NO melodrama, but show people navigating constraints
- Balance factual analysis with individual experiences

## Related Questions (Embedded in Code)

**See:** `lib/prompts.py` - Rule 9

- Generate 3-5 questions based on entities/topics that appeared in documents
- Questions should have SUBSTANTIVE answers (multiple paragraphs)
- Good types: other families mentioned, broader topics, related places/periods
- Bad types: hyper-specific details that only had 1 sentence
- Test: "Could I write multiple paragraphs?" If yes → good question

## Technical Implementation

### Search System
**See:** `lib/search_engine.py`

- **Hybrid Search**: Keyword + semantic for comprehensive coverage
- **Term Grouping**: Defined in `lib/index_builder.py` - `TERM_GROUPS`
- **Name Changes**: Automatically links (e.g., Warburg ↔ DelBanco)
- **Entity Associations**: Dynamically expands queries

### Batch Processing
**See:** `lib/batch_processor.py`

- Handles API rate limiting
- Adaptive batch sizing based on query size
- Configuration in `lib/config.py`

### Prompt Generation
**See:** `lib/prompts.py`

- All prompt templates in one place
- Uses identity data from `lib/identitys.py` (DRY principle)
- Two main prompts: `build_batch_prompt()`, `build_merge_prompt()`

## Hybrid Architecture: Hardcoded + Detected

**Important Note:** "identity" refers to small intermarried elite families (actual cousins/in-laws 
through repeated kinlinks). The data structures here contain broader **identity/attribute** categories 
(religion, ethnicity, gender, race) that apply to all members of a group.

**Location:** `lib/identitys.py` + `lib/identity_detector.py`

### How It Works:

1. **Hardcoded Families** (`HARDCODED_identityS`):
   - Expert knowledge (e.g., "Warburg descended from Sephardi DelBanco")
   - Provides baseline and accuracy
   - Goal: Reduce over time as detector improves

2. **Detected Identities/Attributes** (`lib/identity_detector.py`):
   - Automatically extracts identity/attribute patterns from documents
   - Finds: Religious/ethnic identities, gender (women, widow), racial attributes (Black, African)
   - Example families found: Homberg, Toeplitz, Meisel, Barker, Willing, Neufville, etc.
   - Updates when you run: `python lib/identity_detector.py`

3. **Merged Result** (`identityS`):
   - Combines both: hardcoded (priority) + detected (supplements)
   - Example: Quaker = [Barclay, Lloyd, Bevan, Tritton] + [Barker, Willing, Macy]
   - Detected families marked with `[detected]`

### Multiple Identities (Kinlinks as Bridges):

Families can have multiple identities due to:
- **Ancestry**: Warburg descended from Sephardi DelBanco
- **Conversion**: Hambro (Jewish → converted), Teixeira (Sephardi → associated with Mennonites)
- **Marriage kinlinks**: Schroder (Germanic Protestant) kinlinked with Hambro (converted Jewish)
- **Geographic context**: Different roles in different places

This is normal and expected - kinlinks muddle separation and create bridges across identitys.

### To Improve Detection:

Run the identity/attribute detector to find new families:
```bash
python lib/identity_detector.py
```

This saves results to `data/detected_identitys.json`, which `lib/identitys.py` automatically loads and merges.

## File Structure

```
lib/
├── identitys.py     # identity data (single source of truth)
├── prompts.py         # All prompt templates (loads identitys)
├── search_engine.py   # Search logic
├── batch_processor.py # Rate limiting
├── llm.py             # API calls
├── query_engine.py    # Orchestration
├── index_builder.py   # Index building (includes TERM_GROUPS)
├── document_parser.py # Document parsing
└── config.py          # Configuration

docs/
├── identity_REFERENCE.md  # Comprehensive identity table
└── THUNDERCLAP_GUIDE.md     # This file (framework + preferences)
```

## Key Improvements (From Refactoring)

1. **Zero Duplication**: identity examples in ONE place (`lib/identitys.py`)
2. **Modular**: Each file has single responsibility
3. **Easy Updates**: Change identitys once, affects all prompts
4. **Clean Architecture**: 8 focused modules, 1,400 total lines
5. **Dynamic Search**: Name changes, term grouping, entity associations

## For More Details

- **identity Table**: See `docs/identity_REFERENCE.md`
- **Code**: See `lib/` modules (well-commented)
- **User Interface**: See `README.md`

