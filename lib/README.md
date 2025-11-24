# Library Modules

Core modules for Thunderclap AI identity detection and search system.

## Active Modules (Production)

### Core Search & Query
- **`search_engine.py`** - Vector + keyword search engine
- **`query_engine.py`** - Orchestrates search + LLM narrative generation
- **`batch_processor.py`** - Batches chunks for LLM processing
- **`llm.py`** - LLM wrapper (Gemini)

### Identity Detection (NEW - Optimized)
- **`llm_identity_detector.py`** ⭐ ACTIVE - LLM-based detection
  - Batch processing (3 chunks per call)
  - Multi-attribute detection
  - Intelligent caching
  - 90-95% expected accuracy
  
- **`identity_hierarchy.py`** ⭐ NEW - Hierarchical indexing
  - Maps specific → general (alawite → muslim)
  - Enables searches at any level

- **`api_key_manager.py`** ⭐ NEW - Multi-key rotation
  - Manages 6 API keys (1200 RPD capacity)
  - Auto-rotates on quota exhaustion

### Document Processing
- **`document_parser.py`** - Parses .docx with endnotes
- **`index_builder.py`** - Builds search indices with term grouping
- **`config.py`** - Configuration constants

### Reference Data
- **`identitys.py`** - Hardcoded banking family attributes
- **`prompts.py`** - LLM prompt templates

### Legacy/Transitional
- **`identity_detector.py`** - Current regex detector (47% accuracy)
  - Still active in build_index.py
  - Should be replaced with llm_identity_detector.py tomorrow

---

## Archived Modules (Backup)

Located in `lib/archived/`:

- **`identity_detector_regex_archive.py`** - Backup of regex approach
  - 100+ regex patterns
  - 47% accuracy
  - Can revert if needed

- **`identity_detector_fast.py`** - Earlier optimization attempt
  - Pre-compiled regex patterns
  - No longer needed

---

## Module Dependencies

```
query.py (entry point)
  └─> query_engine.py
       ├─> search_engine.py (ChromaDB vector search)
       ├─> batch_processor.py
       │    └─> llm.py (Gemini)
       └─> prompts.py

build_index.py (indexing entry point)
  ├─> document_parser.py
  ├─> index_builder.py
  │    ├─> identity_hierarchy.py (NEW)
  │    └─> TERM_GROUPS (hardcoded)
  └─> identity_detector.py (TO BE REPLACED)
       or llm_identity_detector.py (NEW, tomorrow)
            ├─> api_key_manager.py (NEW)
            └─> identity_hierarchy.py (NEW)
```

---

## What to Run

### **Daily Use:**
```bash
# Query the system
python query.py "tell me about lebanese bankers"
```

### **After Document Updates:**
```bash
# Rebuild index (uses current detector)
python build_index.py
```

### **Tomorrow (After Midnight PT):**
```bash
# Complete LLM detection with fresh API quota
python scripts/complete_detection_tomorrow.py

# Then rebuild index with LLM results
python build_index.py
```

### **Testing (Optional):**
```bash
# Run experiments
python tests/run_experiments.py

# Test LLM on sample
python tests/test_llm_on_sample.py
```

---

## File Sizes

**Large files (>10KB):**
- `identity_detector.py` - 47.4KB (regex, 765 lines) - to be replaced
- `llm_identity_detector.py` - 19.8KB (LLM, 507 lines) ⭐ NEW
- `index_builder.py` - 17.0KB (405 lines)
- `prompts.py` - 17.1KB (362 lines)

**Most files: 1-6KB** (appropriate size)

---

## Next Steps

1. ✅ Organization complete
2. ⏳ Wait for API quota reset
3. ⏳ Run `scripts/complete_detection_tomorrow.py`
4. ⏳ Replace `identity_detector.py` with `llm_identity_detector.py` in `build_index.py`
5. ⏳ Verify 90%+ accuracy
6. ✅ Delete old regex detector if LLM works well


