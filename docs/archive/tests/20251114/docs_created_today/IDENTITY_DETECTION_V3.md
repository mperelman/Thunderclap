# Identity Detection System v3

## Overview

A 4-step LLM-based identity detection system that enables searching for banking figures by identity attributes (religious, ethnic, racial, gender, nationality) even when those attributes aren't explicitly mentioned in every reference.

**Problem Solved:** Documents mention someone's identity once ("Alawite Salah Jadid"), then use surnames for subsequent references ("Jadid consolidated power"). Without detection, these later references are invisible to identity-based searches.

**Solution:** Extract identity-surname associations from LLM analysis, then search the entire corpus for all surname occurrences to build a comprehensive identity index.

## Architecture: 4-Step Process

### Step 1: Regex Pre-screen
**File:** `lib/identity_prefilter.py`

Fast regex scan to identify chunks containing identity keywords:
- Religious: jewish, muslim, christian, sunni, shia, alawite, quaker, etc.
- Ethnic/Racial: black, white, african, asian, arab, etc.
- Gender: female, male, woman, man, gay, lesbian, etc.
- Nationality: american, british, german, french, etc.

**Performance:** Processes all 1,517 chunks instantly, reducing LLM workload.

### Step 2: LLM Extraction
**File:** `lib/llm_identity_detector.py`

For chunks containing identity keywords, LLM extracts:
- **Surnames**: All family names mentioned
- **Identities**: All attributes for each surname

**Batch Processing:**
- Processes 20 chunks per LLM call
- Caches results in `data/llm_identity_cache.json`
- Uses prompt version tracking to invalidate outdated cache

**Example LLM Output:**
```json
{
  "chunk_1": {
    "jadid": ["alawite", "syrian", "military"],
    "asad": ["alawite", "syrian", "military"]
  }
}
```

**Results:**
- 1,517 total chunks
- 1,017 chunks with identities (67% hit rate)
- 2,262 unique surnames extracted

### Step 3: Surname-Based Search
**File:** `lib/identity_detector_v3.py`

Search entire corpus for ALL occurrences of detected surnames:
- Takes 2,262 surnames from Step 2
- Searches all 1,517 chunks using regex
- Finds 38,754 total surname occurrences
- Average: 17.1 chunks per surname

**Why This Matters:**
- Initial mention: "Alawite Salah Jadid" (chunk 1058)
- Later references: "Jadid's regime" (chunks 1059, 1060, 1061...)
- System finds ALL references to Jadid, not just the first

### Step 4: Index Integration
**File:** `build_index.py` (lines 58-99)

Integrate detected identities into searchable index:
- Loads `data/identity_detection_v3.json`
- Converts integer chunk IDs to string format ("chunk_123")
- Merges with existing text-based search terms
- Saves augmented index to `data/indices.json`

**Results:**
- 342 identity types indexed
- 38,353 new chunk mappings added
- Terms indexed: 19,299 (up from 19,165)

## Detection Results

### Statistics
```
Total identities detected:  342
Unique surnames:           2,262
Surname occurrences:      38,754
LLM processing rate:      67% hit rate
Cache file size:          ~8MB
```

### Top 20 Identities by Coverage
```
christian      1,494 chunks    quaker          1,087 chunks
jewish         1,480 chunks    french          1,078 chunks
american       1,446 chunks    ashkenazi       1,015 chunks
british        1,426 chunks    sephardi          940 chunks
catholic       1,333 chunks    gentile           925 chunks
black          1,332 chunks    female            727 chunks
german         1,289 chunks    court_jew         721 chunks
protestant     1,234 chunks    huguenot          660 chunks
scottish       1,208 chunks    russian           626 chunks
converted      1,169 chunks    bavarian          619 chunks
```

### Hierarchical Coverage Example: "muslim"
```
muslim (general)    356 chunks
├─ sunni            43 chunks (families: Khalifa, Adamjee, Ispahani, etc.)
├─ shia             21 chunks
├─ alawite           7 chunks (families: Jadid, Asad)
├─ ismaili           8 chunks
└─ druze             0 chunks (not explicitly identified)
```

### Specific Examples
```
alawite             7 chunks → Salah Jadid, Hafez Asad
gay                 6 chunks → Martin Chavez, historical references
basque             44 chunks → Basque bankers/merchants
latino/latina   15/12 chunks → Hispanic/Latin American bankers
sunni              43 chunks → Khalifa, Adamjee, Ispahani, Habib families
```

## Query Process: From Search to Narrative

### File: `query.py`

```python
from query import ask

# Generate narrative about any identity
result = ask("tell me about alawite bankers", use_llm=True)
```

### Query Flow

#### 1. Parse Query
```python
query = "tell me about alawite bankers"
use_llm = True  # Generate narrative vs. raw search
```

#### 2. Search Index (Keyword + Semantic)
```python
# Keyword search: term_to_chunks["alawite"]
keyword_chunks = [1058, 1059, 1061, ...]  # 96 matches

# Semantic search: vector similarity
semantic_chunks = [1057, 1060, 1062, ...]  # Top 50

# Combine and deduplicate
combined_chunks = keyword_chunks + semantic_chunks
total_chunks = 96 unique chunks
```

**Identity Index Working:**
- Text mentions: "Alawite Salah Jadid" → chunk 1058
- Detection-based: Later refs to "Jadid" → chunks 1059, 1060, 1061...
- Total: 7 direct + 89 implied = 96 matches

#### 3. Batch Processing for LLM Narrative
```python
# Rate limiting: 15 RPM, 1M TPM, 200 RPD
batch_size = 25 chunks
pause = 6 seconds between batches

# For 50 chunks:
# - Batch 1: 25 chunks
# - Wait 6 seconds
# - Batch 2: 25 chunks
# Total time: ~12 seconds
```

#### 4. LLM Narrative Generation
```python
# Prompt each batch:
"""
You are a banking historian. Create a narrative about [query]
from these document excerpts.

CHUNK 1: [text]
CHUNK 2: [text]
...

Follow Thunderclap framework:
- Subject active in every sentence
- Chronological organization
- Sociological analysis
- No platitudes
"""
```

#### 5. Merge Results
```python
# Combine batch narratives
narrative_1 = "In Syria, the 1960s witnessed..."
narrative_2 = "Following the coup of 1966..."

# LLM merges into coherent narrative
final_narrative = merge_narratives([narrative_1, narrative_2])
```

#### 6. Generate Related Questions
```python
# LLM suggests follow-up questions based on entities mentioned
related_questions = [
    "What role did religious minorities play...",
    "How did the Baath party's policies affect...",
    ...
]
```

### Example: "tell me about sunni"

**Search Results:**
- 43 chunks from identity detection (Sunni families/individuals)
- 97 chunks from text mentions (word "sunni" appears)
- **140 total chunks** (combined)

**LLM Processing:**
- 2 batches (50 chunks, 25 per batch)
- 6 second pause between batches
- ~12 seconds total

**Narrative Output:**
- Chronological: 18th century → 21st century
- Covers: Khalifa family, Wahhab-Saud alliance, Memon families, Nasser's fatwa
- Related questions: 5 specific follow-ups

## Usage

### Basic Search (Raw Results)
```python
from query import ask

# Returns list of matching chunks
results = ask("alawite bankers", use_llm=False)
```

### Narrative Generation (LLM)
```python
from query import ask

# Returns formatted narrative
narrative = ask("tell me about alawite bankers", use_llm=True)
```

### Command Line
```bash
# Raw search
python query.py "sunni bankers"

# LLM narrative (via Python)
python -c "from query import ask; print(ask('tell me about sunni', use_llm=True))"
```

## Files Created/Modified

### New Files
```
lib/llm_identity_detector.py        - Step 2: LLM extraction (v2)
lib/identity_detector_v3.py         - Steps 1-4: Full pipeline
lib/identity_prefilter.py           - Step 1: Regex pre-screen
temp/run_steps_1_2.py               - Script: Run LLM detection
temp/run_steps_3_4.py               - Script: Run surname search + index
temp/verify_index_usage.py          - Verification script
data/identity_detection_v3.json     - Detection results (342 identities)
data/llm_identity_cache.json        - LLM cache (1,017 chunks)
```

### Modified Files
```
build_index.py                      - Added identity integration (lines 58-99)
lib/index_builder.py               - Has augment function (not used in v3)
query.py                           - Existing query interface (unchanged)
```

### Cleaned Up
```
lib/identity_detector.py           - Old detector (kept for reference)
lib/api_key_manager.py            - Deleted (single key approach)
```

## Performance

### LLM Usage
- **Initial detection**: 1,517 chunks processed
- **Cache hit rate**: 100% on subsequent runs
- **API consumption**: ~1,017 LLM calls (batched as 20/call = 51 API calls)

### Search Performance
- **Index lookup**: < 10ms for any identity
- **Result merging**: < 100ms for 50+ chunks
- **Total query time**: 10-20 seconds (LLM narrative generation)

### Storage
```
identity_detection_v3.json:     ~500 KB
llm_identity_cache.json:       ~8 MB
indices.json:                  ~15 MB (with identities)
```

## Maintenance

### Re-run Detection (If Documents Change)
```bash
# Step 1-2: LLM extraction
python temp/run_steps_1_2.py

# Step 3-4: Surname search + index
python temp/run_steps_3_4.py

# Rebuild main index
python build_index.py
```

### Add New Identity Keywords
Edit `lib/identity_prefilter.py`:
```python
IDENTITY_KEYWORDS = [
    # Add new keywords here
    'new_identity_term',
]
```

### Adjust Hierarchies
Edit `lib/identity_hierarchy.py` (if needed):
```python
IDENTITY_HIERARCHY = {
    'muslim': ['sunni', 'shia', 'alawite', 'ismaili'],
    # Add new hierarchies
}
```

## Limitations

1. **Surname ambiguity**: Common surnames (Smith, Brown) may cause false positives
2. **Name changes**: Married names, adoptions not fully tracked
3. **Implied identities**: LLM may miss subtle identity markers
4. **Single mentions**: Individuals mentioned once may not be caught
5. **Language**: English-only detection

## Future Enhancements

1. **Confidence scoring**: Weight detections by LLM confidence
2. **Temporal tracking**: Identity changes over time (conversions)
3. **Relationship mapping**: Family connections, marriages
4. **Multi-language**: Extend to non-English documents
5. **Active learning**: User feedback to improve detection

