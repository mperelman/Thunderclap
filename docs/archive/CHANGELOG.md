# Changelog

All notable changes to Thunderclap AI will be documented in this file.

## [1.0.0] - 2025-11-10

### Added
- **Identity Search Integration** - Search index now enhanced with detected family identities
  - Searching "black bankers" finds Richard Parsons, Raymond McGuire, etc. (not just explicit mentions)
  - Works for all 22 identity types (religious, ethnic, gender, racial, nationality)
  - Implemented in `lib/index_builder.py::augment_indices_with_identities()`
  - Auto-runs during `python build_index.py`

- **API Key Auto-Loading** - `.env` file support with python-dotenv
  - No more manual `$env:GEMINI_API_KEY` every session
  - Added to `requirements.txt` and `query.py`
  - See `docs/API_KEY_SETUP.md` for setup

- **Identity Detector** - Dynamic extraction of 22 identity/attribute types
  - Precise regex patterns (not proximity matching)
  - ~75% precision for Black identity (validated)
  - Noise filtering (150+ noise words)
  - Saves to `data/detected_identitys.json`

- **Documentation**
  - `docs/ARCHITECTURE.md` - Comprehensive system design
  - `docs/API_KEY_SETUP.md` - API key setup guide  
  - `docs/QUICK_FIX.md` - Quick troubleshooting
  - `docs/CODEBASE_REVIEW.md` - Code quality review

### Changed
- **Index Builder** - Now runs identity detector automatically during indexing
- **Query Module** - Auto-loads `.env` file on import
- **Requirements** - Added `python-dotenv>=1.0.0`
- **Documentation** - Consolidated 4 similar docs into `ARCHITECTURE.md`

### Fixed
- **Search Recall** - Identity searches now find 4x more results
  - "black bankers": 50 → 193 chunks
  - Includes detected families, not just explicit mentions
- **API Key Issue** - Prevented "no narrative generated" problem
  - `.env` file ensures key is always loaded
  - No more manual environment variable setting

### Removed
- Duplicate documentation files (IDENTITY_INDEX_INTEGRATION, SESSION_SUMMARY, etc.)
- Temporary output files from root directory
- Utility scripts from root (moved to `scripts/`)

## [0.9.0] - Previous Version (Before Session)

### Features
- Keyword + vector search
- Endnote linking
- Batch processing with rate limiting
- Thunderclap narrative framework
- Hardcoded identity data
- Term grouping in search index

### Architecture
- Clean module separation
- ChromaDB for vector search
- Adaptive batch sizing
- Graceful degradation (works without LLM)

## Future Enhancements

### Planned
- Unit tests for core modules
- Example notebooks in `examples/` directory
- Kinship network analysis (detect true identitys)
- Enhanced confidence scoring for detected identities

### Under Consideration
- Alternative embedding models
- Multilingual support
- Real-time index updates
- Web interface

---

*Format based on [Keep a Changelog](https://keepachangelog.com/)*


