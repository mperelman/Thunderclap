# Thunderclap AI - System Overview

## What Is Thunderclap?

A specialized search and narrative generation system for banking history documents. Built to enable identity-based searches (religious, ethnic, racial, gender, nationality) and generate historically accurate narratives following specific scholarly frameworks.

## Core Capabilities

### 1. Identity-Aware Search
Search for banking figures by identity attributes, even when not explicitly mentioned every time:
- **Religious**: Jewish, Muslim (Sunni, Shia, Alawite), Christian, Quaker, Huguenot
- **Ethnic/Racial**: Black, Asian, Arab, Levantine, Basque, Latino
- **Gender/Orientation**: Female, Male, Gay, Lesbian
- **Nationality**: American, British, German, French, Japanese, Nigerian, etc.

### 2. LLM Narrative Generation
Generates historically accurate narratives from search results following Thunderclap framework:
- Subject-active voice
- Chronological organization
- Sociological analysis (cousinhoods, minority middlemen, kinlinks)
- No platitudes or flowery language
- Cited evidence from endnotes

### 3. Hierarchical Search
Automatically includes specific terms when searching general categories:
- Search "muslim" → finds sunni, shia, alawite, ismaili
- Search "jewish" → finds sephardi, ashkenazi, mizrahi, court_jew
- Search "black" → finds african_american, hausa, yoruba, igbo

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                           │
│  query.py: ask("tell me about sunni bankers", use_llm=True) │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SEARCH ENGINE                             │
│  lib/query_engine.py: Keyword + Semantic Search              │
│  • Term index lookup (O(1))                                  │
│  • Vector database similarity                                │
│  • Result merging & deduplication                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  IDENTITY-AUGMENTED INDEX                    │
│  data/indices.json (19,299 terms)                            │
│  • Text-based terms: 19,165 terms                            │
│  • Identity-based: 342 identities → 38,353 mappings          │
│  • Hierarchical groupings                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴────────────┐
                ▼                          ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   TERM INDEX             │  │  IDENTITY DETECTION v3    │
│   lib/index_builder.py   │  │  4-Step Process          │
│   • Regex extraction     │  │  1. Regex pre-screen     │
│   • Name changes         │  │  2. LLM extraction       │
│   • Term grouping        │  │  3. Surname search       │
└──────────────────────────┘  │  4. Index integration    │
                              └──────────────────────────┘
                                          │
                    ┌─────────────────────┴───────────────┐
                    ▼                                      ▼
        ┌─────────────────────┐              ┌────────────────────────┐
        │  LLM DETECTOR        │              │  DOCUMENT CORPUS       │
        │  lib/llm_identity_   │              │  3 documents           │
        │  detector.py         │              │  • Part I (2,263 ¶)   │
        │  • Batch processing  │              │  • Part II (2,606 ¶)  │
        │  • Caching (v2)      │              │  • Part III (2,655 ¶) │
        │  • 67% hit rate      │              │  -------------------- │
        └─────────────────────┘              │  1,517 chunks          │
                                              │  14,094 endnotes      │
                                              └────────────────────────┘
```

## Data Flow: Query to Narrative

### Example: "tell me about sunni bankers"

```
1. QUERY PARSING
   Input: "tell me about sunni bankers"
   Mode: use_llm=True (narrative generation)

2. SEARCH INDEX
   ├─ Keyword: term_to_chunks["sunni"] → 140 chunks
   │  ├─ Text mentions: 97 chunks (word "sunni" in text)
   │  └─ Identity detection: 43 chunks (Sunni individuals)
   ├─ Semantic: vector_db.similarity("sunni bankers") → 50 chunks
   └─ Combined: 140 unique chunks

3. LLM PROCESSING (Batched)
   ├─ Batch 1: 25 chunks → narrative_1
   ├─ Wait 6 seconds (rate limiting)
   ├─ Batch 2: 25 chunks → narrative_2
   └─ Merge: narrative_1 + narrative_2 → final narrative

4. OUTPUT
   ├─ Narrative: Chronological, 18th → 21st century
   ├─ Families: Khalifa, Adamjee, Ispahani, Habib
   └─ Related questions: 5 follow-ups

Total time: ~12 seconds
```

## Key Files

### Core System
```
build_index.py                      - Main index builder (with identity integration)
query.py                            - Query interface (search + narrative)
```

### Libraries
```
lib/
├── document_parser.py              - Parse .docx files (body + endnotes)
├── index_builder.py                - Build term indices
├── query_engine.py                 - Search orchestration
├── llm.py                          - LLM API wrapper
├── prompts.py                      - Prompt templates
├── identity_detector_v3.py         - 4-step identity detection
├── llm_identity_detector.py        - LLM-based extraction (Step 2)
├── identity_prefilter.py           - Regex pre-screen (Step 1)
├── identity_hierarchy.py           - Hierarchical mappings
└── config.py                       - Configuration
```

### Data Files
```
data/
├── indices.json                    - Main search index (19,299 terms)
├── identity_detection_v3.json      - Detection results (342 identities)
├── llm_identity_cache.json         - LLM cache (1,017 chunks)
├── endnotes.json                   - All endnotes (14,094)
├── chunk_to_endnotes.json          - Chunk → endnote mappings
└── vectordb/                       - ChromaDB vector database
```

### Documentation
```
docs/
├── SYSTEM_OVERVIEW.md              - This file
├── IDENTITY_DETECTION_V3.md        - Identity detection deep dive
├── THUNDERCLAP_GUIDE.md            - Narrative framework rules
└── IDENTITY_SEARCH_INTEGRATION.md  - Search integration details
```

### Utilities
```
scripts/
├── verify_identity_index.py        - Verify index integration
└── run_batch_detection.py          - Run Batch API detection
```

## Usage Examples

### 1. Basic Search (Raw Results)
```python
from query import ask

# Returns list of matching chunks
results = ask("alawite bankers", use_llm=False)
```

### 2. Narrative Generation
```python
from query import ask

# Returns formatted narrative
narrative = ask("tell me about sunni bankers", use_llm=True)
```

### 3. Command Line
```bash
# Raw search
python query.py "quaker bankers"

# Narrative (via Python)
python -c "from query import ask; print(ask('tell me about black bankers', use_llm=True))"
```

### 4. Hierarchical Search
```python
# General category includes all specific terms
ask("muslim bankers", use_llm=True)  
# → Finds: sunni, shia, alawite, ismaili, druze

ask("jewish bankers", use_llm=True)
# → Finds: sephardi, ashkenazi, mizrahi, court_jew
```

## Performance Metrics

### Search Speed
- **Index lookup**: < 10ms
- **Vector similarity**: ~100ms
- **Result merging**: < 50ms
- **Total search**: ~150ms

### LLM Narrative
- **Batch size**: 25 chunks
- **Rate limit**: 15 RPM, 1M TPM, 200 RPD
- **Typical query**: 2 batches (~12 seconds)
- **Large query**: 4 batches (~30 seconds)

### Storage
```
Document corpus:      ~15 MB (3 .docx files)
Search index:         ~15 MB (19,299 terms)
Identity detection:   ~500 KB (342 identities)
LLM cache:            ~8 MB (1,017 cached results)
Vector database:      ~20 MB (1,517 embeddings)
Endnotes:             ~10 MB (14,094 notes)
--------------------
Total:                ~70 MB
```

### Detection Statistics
```
Total documents:         3
Total paragraphs:       7,524
Total chunks:           1,517
Total endnotes:        14,094

Identity detection:
├─ Identities found:    342
├─ Surnames extracted:  2,262
├─ Occurrences:        38,754
└─ LLM hit rate:        67%

Index statistics:
├─ Terms indexed:      19,299
├─ Chunk mappings:     605,097
├─ Term groups:         35
└─ Name changes:        37
```

## Maintenance

### Re-index After Document Changes
```bash
# Full rebuild (includes identity detection)
python build_index.py
```

### Re-run Identity Detection Only
```bash
# If detection logic changes
python scripts/run_identity_detection.py  # Steps 3-4
python build_index.py                     # Rebuild index
```

### Verify Index Integrity
```bash
# Check identity integration
python scripts/verify_identity_index.py
```

### Clear Caches
```bash
# Clear LLM cache (force re-detection)
del data\llm_identity_cache.json

# Clear all indices (force full rebuild)
del data\indices.json
del data\identity_detection_v3.json
```

## Configuration

### Environment Variables
```bash
# Required: Gemini API key
GEMINI_API_KEY=your_key_here

# Optional: Rate limiting
GEMINI_RPM=15          # Requests per minute
GEMINI_TPM=1000000     # Tokens per minute
GEMINI_RPD=200         # Requests per day
```

### lib/config.py
```python
# Document settings
CHUNK_SIZE = 500           # Words per chunk
CHUNK_OVERLAP = 100        # Overlapping words

# Search settings
MIN_TERM_FREQUENCY = 2     # Minimum term occurrences

# LLM settings
DEFAULT_MODEL = "gemini-2.0-flash"
BATCH_SIZE = 20            # Chunks per LLM call
PAUSE_SECONDS = 6          # Pause between batches
```

## Thunderclap Framework

### Narrative Principles
1. **Relevance**: Only information directly involving query subject
2. **Accuracy**: Never fabricate; state only what documents say
3. **Subject Active**: Subject active in every sentence
4. **Chronological**: Strict time periods, never jump backwards
5. **Sociology**: Analyze identity/networks/exclusion in EVERY section
6. **Panics**: Cover all financial crises mentioned
7. **No Platitudes**: Avoid "dynamic nature", "testament to", etc.

### Writing Style
- **Bernanke**: Analytical rigor, factual precision
- **Maya Angelou**: Humanizing details, individual experiences
- **Balance**: Facts + humanity, no melodrama

### Naming Conventions
- **Institutions**: Italics (*Hope*, *Lehman*)
- **People**: Regular text (Henry Hope, Henry Lehman)
- **No "& Co."**: Causes incorporation confusion

See `docs/THUNDERCLAP_GUIDE.md` for complete framework.

## Troubleshooting

### "No results found"
- Check if term exists in index: `grep "term" data/indices.json`
- Verify identity detection ran: Check `data/identity_detection_v3.json`
- Try broader search: "muslim" instead of "alawite"

### "Rate limit exceeded"
- Default: 15 RPM, check usage in last minute
- Increase pause: Edit `PAUSE_SECONDS` in `lib/config.py`
- Use fewer chunks: Set `max_chunks=10` in query

### "Index not found"
- Run: `python build_index.py`
- Check: `data/indices.json` exists

### "Identity not detected"
- Check prefilter has keyword: `lib/identity_prefilter.py`
- Re-run detection: `python scripts/run_identity_detection.py`
- Verify LLM cache: Check `data/llm_identity_cache.json`

## Future Enhancements

### Planned Features
1. **Multi-lingual support**: Extend beyond English
2. **Temporal tracking**: Identity changes over time
3. **Confidence scoring**: Weight detections by LLM confidence
4. **Relationship mapping**: Family connections, marriages
5. **Active learning**: User feedback to improve detection

### Research Extensions
1. **Network analysis**: Visualize kinship networks
2. **Comparative analysis**: Cross-identity patterns
3. **Crisis tracking**: Systematic panic analysis
4. **Geographic mapping**: Spatial distribution of families

## Contact & Support

- **Documentation**: `docs/` folder
- **Examples**: See `docs/IDENTITY_DETECTION_V3.md`
- **Verification**: Run `scripts/verify_identity_index.py`

