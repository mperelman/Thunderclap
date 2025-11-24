# Cleanup Plan - Organized Codebase

## Actions to Execute

### 1. Move Obsolete Code to Archive

**Cousinhood files (user rejected terminology):**
```
lib/cousinhood_detector.py → lib/archived/rejected/
lib/cousinhoods.py → lib/archived/rejected/
```

**API key manager (user said forget):**
```
lib/api_key_manager.py → lib/archived/rejected/
```

**Failed experiments:**
```
lib/batch_processor_twopass.py → lib/archived/experiments/
lib/prompts_twopass.py → lib/archived/experiments/
```

### 2. Move Root Test Scripts to temp/

```
detector_summary.py → temp/old_scripts/
get_black_bankers.py → temp/old_scripts/
show_banking_families.py → temp/old_scripts/
show_black_bankers.py → temp/old_scripts/
show_precise_matches.py → temp/old_scripts/
test_black_detector.py → temp/old_scripts/
test_brahmin_disambiguation.py → temp/old_scripts/
```

### 3. Move Root Documentation to docs/archive/

```
ARCHITECTURE_REVIEW.md → docs/archive/sessions/
BLACK_BANKERS_COMPREHENSIVE.md → docs/archive/sessions/
CODEBASE_REVIEW.md → docs/archive/sessions/
DETECTOR_RENAME_SUMMARY.md → docs/archive/sessions/
DYNAMIC_COUSINHOODS_PROPOSAL.md → docs/archive/sessions/
IDENTITY_DETECTION_STATUS.md → docs/archive/sessions/
PROJECT_STRUCTURE.md → docs/archive/sessions/
QUICK_FIX.md → docs/archive/sessions/
TOMORROW_CHECKLIST.md → docs/archive/sessions/
```

### 4. Consolidate Scripts

**Keep (core utilities):**
- verify_identity_index.py
- show_all_identities.py
- run_identity_detection.py
- add_panic_indexing_simple.py
- README.md

**Archive (obsolete tests):**
```
scripts/test_*.py → temp/old_scripts/
scripts/debug_*.py → temp/old_scripts/
scripts/find_*.py → temp/old_scripts/
scripts/auto_run_when_ready.py → temp/old_scripts/
scripts/complete_detection_tomorrow.py → temp/old_scripts/
scripts/verify_all_detections.py → temp/old_scripts/
scripts/verify_index_usage.py → temp/old_scripts/ (duplicate of verify_identity_index.py)
scripts/add_panic_indexing.py → temp/old_scripts/ (keep _simple version)
```

### 5. Consolidate Documentation

**Keep (current/relevant):**
- docs/THUNDERCLAP_GUIDE.md (narrative framework)
- docs/IDENTITY_SEARCH_INTEGRATION.md (identity system)
- docs/README.md (if exists)

**Archive (session-specific or obsolete):**
```
docs/API_KEY_SETUP.md → docs/archive/
docs/ARCHITECTURE_REVIEW.md → docs/archive/
docs/ARCHITECTURE.md → docs/archive/
docs/CHANGELOG.md → docs/archive/
docs/CLEANUP_SUMMARY.md → docs/archive/sessions/
docs/CODEBASE_REVIEW.md → docs/archive/sessions/
docs/COUSINHOOD_REFERENCE.md → docs/archive/rejected/
docs/FINAL_DETECTION_SYSTEM.md → docs/archive/
docs/IDENTITY_DETECTION_EXPERIMENTS.md → docs/archive/experiments/
docs/IDENTITY_DETECTOR_IMPROVEMENTS.md → docs/archive/
docs/IDENTITY_DETECTOR.md → docs/archive/
docs/IDENTITY_INDEX_INTEGRATION.md → docs/archive/
docs/LGBT_LATINO_APPROACH.md → docs/archive/
docs/LLM_DETECTOR_GUIDE.md → docs/archive/
docs/PREFERENCES_SUMMARY.md → docs/archive/
docs/QUICK_FIX.md → docs/archive/sessions/
docs/SESSION_SUMMARY.md → docs/archive/sessions/
docs/SOCIOLOGICAL_PATTERNS.md → docs/archive/
docs/THUNDERCLAP_FRAMEWORK.md → docs/archive/ (if duplicate of THUNDERCLAP_GUIDE.md)
```

## Final Clean Structure

```
thunderclap-ai/
├── query.py
├── build_index.py
├── README.md
│
├── lib/
│   ├── config.py
│   ├── document_parser.py
│   ├── index_builder.py
│   ├── llm.py
│   ├── prompts.py
│   ├── query_engine.py
│   ├── search_engine.py
│   ├── batch_processor.py
│   ├── batch_processor_iterative.py
│   ├── batch_processor_geographic.py
│   ├── panic_indexer.py
│   ├── identity_hierarchy.py
│   ├── identity_detector_v3.py
│   ├── llm_identity_detector.py
│   ├── identity_prefilter.py
│   └── archived/
│       ├── archived_20251113_RESTORED/
│       ├── experiments/
│       └── rejected/
│
├── scripts/
│   ├── verify_identity_index.py
│   ├── show_all_identities.py
│   ├── run_identity_detection.py
│   ├── add_panic_indexing_simple.py
│   └── README.md
│
├── docs/
│   ├── THUNDERCLAP_GUIDE.md
│   ├── IDENTITY_SEARCH_INTEGRATION.md
│   └── archive/
│       ├── sessions/
│       ├── experiments/
│       └── rejected/
│
├── data/ (gitignored)
└── temp/ (gitignored)
```

Execute this cleanup?




