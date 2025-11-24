# Thunderclap AI - Project Structure

**Current Status:** Optimized LLM detection system ready for deployment tomorrow

---

## 📁 Directory Structure

```
thunderclap-ai/
│
├── 📄 TOMORROW_CHECKLIST.md          ⭐ READ THIS FIRST
├── 📄 IDENTITY_DETECTION_STATUS.md   ⭐ System overview
├── 📄 PROJECT_STRUCTURE.md            (this file)
├── 📄 README.md                       Main project README
├── 📄 requirements.txt                Python dependencies
├── 📄 .cursorrules                    AI assistant rules
├── 📄 .env                            6 API keys configured
│
├── 📂 lib/                            Core modules (13 files)
│   ├── llm_identity_detector.py      ⭐ NEW - LLM detection (19.8KB)
│   ├── api_key_manager.py            ⭐ NEW - 6-key rotation (3.4KB)
│   ├── identity_hierarchy.py         ⭐ NEW - Hierarchical indexing (3.3KB)
│   ├── identity_detector.py          📋 CURRENT - Regex (47.4KB, 47% accuracy)
│   ├── query_engine.py               Query orchestration
│   ├── search_engine.py              Vector + keyword search
│   ├── index_builder.py              Index building (17KB)
│   ├── batch_processor.py            LLM batching
│   ├── llm.py                         Gemini wrapper
│   ├── prompts.py                     Prompt templates (17.1KB)
│   ├── identitys.py                 Hardcoded families (8.8KB)
│   ├── document_parser.py             .docx parser
│   ├── config.py                      Configuration
│   ├── README.md                      Module docs
│   └── archived/                      Old approaches (backup)
│       ├── identity_detector_regex_archive.py  (47.4KB)
│       └── identity_detector_fast.py           (16KB)
│
├── 📂 scripts/                        Production scripts
│   ├── complete_detection_tomorrow.py ⭐ RUN TOMORROW
│   └── analyze_attributes.py          Utility
│
├── 📂 tests/                          Test/experimental scripts
│   ├── run_experiments.py             Compare approaches
│   ├── test_llm_on_sample.py          Test on 10 chunks
│   └── README.md                      Test documentation
│
├── 📂 docs/                           Documentation (14 files)
│   ├── FINAL_DETECTION_SYSTEM.md      Complete architecture
│   ├── IDENTITY_DETECTION_EXPERIMENTS.md  Experiment designs
│   ├── THUNDERCLAP_GUIDE.md           User guide
│   ├── identity_REFERENCE.md        Family reference
│   ├── API_KEY_SETUP.md               API configuration
│   ├── ARCHITECTURE.md                System architecture
│   ├── CHANGELOG.md                   Version history
│   ├── CLEANUP_SUMMARY.md             Cleanup notes
│   ├── IDENTITY_DETECTOR.md           Detector docs
│   ├── LLM_DETECTOR_GUIDE.md          LLM guide
│   └── ... (other docs)
│
├── 📂 data/
│   ├── documents/                     Source .docx files (3)
│   ├── cache/                         Parsed .docx (3 .json)
│   ├── indices.json                   Search index
│   ├── detected_identities.json       Detection results
│   ├── llm_identity_cache.json        LLM cache (1100/1515)
│   ├── endnotes.json                  Endnote database
│   └── chunk_to_endnotes.json         Chunk mappings
│
├── 📄 build_index.py                  Build search index
├── 📄 query.py                        Query interface
└── 📂 chroma_db/                      Vector database


