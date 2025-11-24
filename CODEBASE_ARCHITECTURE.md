# Thunderclap AI - Codebase Architecture
**Last Updated:** November 14, 2024  
**Status:** Production-ready

## 📁 Directory Structure

```
thunderclap-ai/
├── server.py                      # ⭐ Main FastAPI server (use this)
├── query.py                       # CLI interface
├── build_index.py                 # Index builder
├── simple_frontend.html           # Web UI
├── START_SERVER.bat               # Server launcher
├── TEST_API.bat                   # API tester
├── requirements.txt               # Dependencies
├── README.md                      # Project overview
├── .cursorrules                   # AI assistant rules
├── .env                           # API keys (gitignored)
├── .gitignore                     # Git ignore rules
│
├── lib/                           # Core library modules
│   ├── query_engine.py            # ⭐ Main query coordinator
│   ├── batch_processor_iterative.py  # ⭐ Time-period processor
│   ├── batch_processor_geographic.py # ⭐ Geographic/event processor
│   ├── llm.py                     # ⭐ LLM API wrapper
│   ├── prompts.py                 # ⭐ Prompt templates & rules
│   ├── identity_hierarchy.py      # Identity search expansion
│   ├── index_builder.py           # Index construction
│   ├── document_parser.py         # Document processing
│   ├── identity_detector_v3.py    # Identity detection
│   ├── identity_prefilter.py      # Identity prefiltering
│   ├── llm_identity_detector.py   # LLM-based identity detection
│   ├── panic_indexer.py           # Panic term indexing
│   ├── config.py                  # Configuration
│   │
│   ├── archived/                  # Old implementations (for reference)
│   ├── archived_20251113_RESTORED/ # Recovered files
│   └── archived_20251114_CLEANUP/  # Today's cleanup
│
├── data/                          # Database & indices (gitignored)
│   ├── indices.json               # Term index
│   ├── endnotes.json              # Genealogical data
│   ├── chunk_to_endnotes.json     # Chunk-endnote mapping
│   ├── detected_identities.json   # Identity detection results
│   ├── cache/                     # Document parsing cache
│   └── vectordb/                  # ChromaDB vector database
│
├── source_documents/              # Source materials (gitignored)
│   ├── Thunderclap Part I.docx
│   ├── Thunderclap Part II.docx
│   └── Thunderclap Part III.docx
│
├── docs/                          # Documentation
│   ├── THUNDERCLAP_GUIDE.md       # User guide
│   ├── USER_PREFERENCES.md        # Narrative preferences
│   ├── IDENTITY_SEARCH_INTEGRATION.md
│   ├── SECURE_DEPLOYMENT.md
│   └── archive/                   # Old documentation
│
├── scripts/                       # Utility scripts
│   ├── run_identity_detection.py
│   ├── show_all_identities.py
│   ├── verify_identity_index.py
│   └── analyze_attributes.py
│
├── temp/                          # Temporary files (gitignored)
│   └── archived_tests_20251114/   # Archived test scripts
│
└── tests/                         # Test suite
    ├── run_experiments.py
    ├── safe_incremental_test.py
    └── test_llm_on_sample.py
```

## 🏗️ Architecture Overview

### Query Processing Flow

```
User Question
    ↓
query_engine.py (QueryEngine)
    ↓
Auto-detects query type:
    ├── Event query (panic, crisis, war) → batch_processor_geographic.py
    │   └── Organizes by: Geography/Sector
    │
    └── Topic query (families, groups) → batch_processor_iterative.py
        └── Organizes by: Time Periods
    ↓
llm.py (LLM wrapper)
    ↓
Gemini API (2.0 Flash)
    ↓
Formatted narrative output
```

### Processing Modes

**Sequential Mode (Current - FastAPI compatible):**
- `use_async=False` in server.py
- 5-second delays between API calls
- Respects 15 RPM rate limit
- Stable, no event loop conflicts
- Slower (~40-50s for large queries)

**Async Mode (Future - when event loop issues fixed):**
- `use_async=True` in server.py
- Concurrent API calls with semaphore
- 5x faster (~10s for large queries)
- Requires event loop fix for FastAPI

### Module Responsibilities

#### Core Modules

**`query_engine.py`** - Main coordinator
- Search term expansion (identity hierarchy)
- Chunk retrieval from vector DB
- Query type detection (event vs topic)
- Endnote augmentation for sparse results
- Routes to appropriate processor

**`batch_processor_iterative.py`** - Time-period processor
- For broad topics (families, groups, identities)
- Organizes chunks by time period
- Generates period narratives
- Combines into chronological narrative
- Both sequential and async versions

**`batch_processor_geographic.py`** - Geographic/event processor
- For specific events (panics, crises, wars)
- Organizes chunks by geography/sector
- Generates regional narratives
- Combines into comprehensive narrative
- Both sequential and async versions

**`llm.py`** - LLM interface
- Wrapper for Gemini API
- Both sync and async methods
- Error handling and retries
- Rate limit management

**`prompts.py`** - Centralized prompts
- All prompt templates
- Narrative style rules
- Thunderclap framework guidelines
- Suggested questions rules

#### Supporting Modules

**`identity_hierarchy.py`** - Search expansion
- Maps specific → broad identities
- Example: 'dalit' → 'hindu'
- Enables comprehensive searches

**`index_builder.py`** - Index construction
- Builds term index from documents
- Panic indexing (Panic of 1907, etc)
- Identity integration

**`document_parser.py`** - Document processing
- Parses Word documents
- Extracts text and endnotes
- Caching for performance

**`identity_detector_v3.py`** - Identity detection
- Finds people's identities in text
- Tracks religion, ethnicity, nationality, etc.
- Caches results for efficiency

**`panic_indexer.py`** - Panic term indexing
- Indexes specific panic years
- Ensures "Panic of 1914" retrieves only 1914 content

## 🚀 Usage

### Starting the Server

```bash
# Option 1: Double-click
START_SERVER.bat

# Option 2: Command line
python server.py
```

### Testing the API

```bash
# Option 1: Double-click
TEST_API.bat

# Option 2: Command line
curl http://localhost:8000/health
```

### Using the Web Interface

1. Start server (START_SERVER.bat)
2. Open simple_frontend.html in browser
3. Ask questions about banking history

### CLI Usage

```bash
# Set API key
$env:GEMINI_API_KEY = 'your-key-here'

# Ask a question
python query.py "tell me about Lehman"

# With LLM narrative
python query.py "tell me about Jewish bankers"
```

## 🔧 Configuration

### Environment Variables

Create `.env` file:
```
GEMINI_API_KEY_1=AIza...
GEMINI_API_KEY_2=AIza...
# ... up to 6 keys for rotation
```

### Toggle Async Mode

In `server.py`, line 38:
```python
# Sequential (current - stable)
query_engine = QueryEngine(gemini_api_key=gemini_key, use_async=False)

# Async (future - when fixed)
query_engine = QueryEngine(gemini_api_key=gemini_key, use_async=True)
```

## 📊 Database

**Vector Database:** ChromaDB (1,517 chunks)  
**Term Index:** 19,330 searchable terms  
**Endnotes:** 14,094 genealogical records  
**Panics Indexed:** 31 financial crises (1763-2008)  

## 🎯 Design Principles

1. **Modularity** - Each processor has sequential + async versions
2. **Auto-detection** - System chooses best processor for query type
3. **One-line toggle** - Switch between modes with single flag
4. **No duplication** - Shared code in base classes
5. **Clean separation** - Query coordination, processing, LLM separate
6. **Rate limit aware** - Built-in delays for API limits
7. **Comprehensive search** - Identity hierarchy for broad searches
8. **Sparse result handling** - Endnote augmentation when needed

## 🗂️ Archived Code

### `lib/archived_20251114_CLEANUP/`
- `batch_processor.py` - Old batch processor (replaced by iterative/geographic)
- `search_engine.py` - Old search implementation
- `secure_api.py` - Old API server (replaced by server.py)
- `working_api.py` - Temp server file
- `simple_test_server.py` - Temp test server

### `lib/archived_20251113_RESTORED/`
- Files recovered from .pyc after accidental deletion
- Preserved for historical reference

### `lib/archived/`
- Old identity detector versions
- Rejected implementations
- Experimental features

### `temp/archived_tests_20251114/`
- All test scripts from development
- Investigation and debugging scripts
- Temporary documentation

## 🔐 Security

- No raw document access via API
- No code execution endpoints
- Rate limiting (20 requests/hour)
- CORS configured
- API keys in .env (gitignored)
- Source documents gitignored
- Database gitignored

## 📝 Key Files to Know

**For Development:**
- `lib/query_engine.py` - Start here
- `lib/batch_processor_iterative.py` - Time-period processing
- `lib/batch_processor_geographic.py` - Geographic processing
- `lib/prompts.py` - Narrative rules
- `.cursorrules` - AI assistant instructions

**For Deployment:**
- `server.py` - Main server
- `simple_frontend.html` - Web UI
- `START_SERVER.bat` - Launcher
- `requirements.txt` - Dependencies

**For Maintenance:**
- `build_index.py` - Rebuild index
- `scripts/run_identity_detection.py` - Update identities
- `TEST_API.bat` - Test after changes

## 🎨 Narrative Style

See `docs/USER_PREFERENCES.md` for complete rules:
- Short paragraphs (3-4 sentences)
- Chronological organization
- Cultural/sociological analysis
- Subject-active voice
- No platitudes
- Institutions in italics
- Comprehensive coverage

## ✅ Current Status

- ✅ Sequential processing working perfectly
- ✅ Both processors (iterative + geographic) functional
- ✅ Rate limiting implemented
- ✅ Web interface clean and functional
- ✅ Codebase organized and documented
- ✅ Archived old/unused code
- ⏳ Async mode ready (needs event loop fix)

---

**For Questions:** See docs/ folder or .cursorrules for detailed guidelines



