# Changelog

## [v3.0] - 2025-11-12: Identity Detection System

### Major Features Added

#### Identity Detection System v3
- **4-step LLM-based detection pipeline**: Regex pre-screen → LLM extraction → Surname search → Index integration
- **342 identity types** indexed across religious, ethnic, racial, gender, and nationality categories
- **38,754 surname occurrences** tracked across 1,517 document chunks
- **67% LLM hit rate** (1,017/1,517 chunks contained identity information)

#### Identity-Aware Search
- Search by identity attributes even when not explicitly mentioned
- Hierarchical search: General terms include specific categories
  - "muslim" → sunni, shia, alawite, ismaili
  - "jewish" → sephardi, ashkenazi, mizrahi, court_jew
- Combined text-based and detection-based results

#### Enhanced Index Integration
- Identity mappings integrated into main search index
- 38,353 new chunk mappings from identity detection
- Terms indexed increased from 19,165 → 19,299

### New Files

#### Core Detection
- `lib/identity_detector_v3.py` - Complete 4-step detection pipeline
- `lib/llm_identity_detector.py` - LLM-based extraction (Step 2, v2)
- `lib/identity_prefilter.py` - Fast regex pre-screen (Step 1)
- `lib/identity_hierarchy.py` - Hierarchical identity mappings

#### Data Files
- `data/identity_detection_v3.json` - Detection results (342 identities, 2,262 surnames)
- `data/llm_identity_cache.json` - LLM response cache (1,017 processed chunks)

#### Documentation
- `docs/IDENTITY_DETECTION_V3.md` - Complete detection system documentation
- `docs/SYSTEM_OVERVIEW.md` - System architecture and usage guide
- `CHANGELOG.md` - This file

#### Scripts
- `scripts/verify_identity_index.py` - Verify index integration
- `scripts/show_all_identities.py` - Display all detected identities
- `scripts/run_identity_detection.py` - Run detection Steps 3-4
- `scripts/README.md` - Script documentation

### Modified Files

#### build_index.py
- **Lines 58-99**: Added identity detection integration
- Loads `data/identity_detection_v3.json`
- Converts integer chunk IDs to string format
- Merges identity mappings with existing term index
- Reports 38,353 new chunk mappings added

#### query.py
- No functional changes
- Works seamlessly with identity-augmented index

### Removed Files

#### Deleted
- `lib/api_key_manager.py` - Removed multi-key rotation (single key approach)

#### Cleaned Up temp/
- Moved documentation to `docs/archive/`:
  - BATCH_API_GUIDE.md
  - CODEBASE_REVIEW.md
  - COMPLETE_DETECTION_FLOW.md
  - DETECTOR_CLEANUP_PLAN.md
  - DETECTOR_EXPLANATION.md
  - FINAL_4_STEP_ARCHITECTURE.md
  - ROTATION_FIX_SUMMARY.md
  - check_quota_reset_time.md
  - identity_detection_summary.md
  - TEMP_README.md

- Deleted obsolete test/diagnostic scripts:
  - check_accessible_keys.py
  - check_llm_output.py
  - diagnose_error.py
  - find_detected_identities.py
  - find_key.py
  - list_batch_models.py
  - run_at_3am.py
  - run_detection_conservative.py
  - show_detected_identities.py
  - show_raw_error.py
  - single_clean_call.py
  - test_banker_chunks.py
  - test_on_identity_chunks.py
  - test_quota_reset.py
  - test_vernon.py
  - batch_requests.jsonl
  - panic_1837_result.txt
  - vernon_jordan.txt

- Moved utility scripts to `scripts/`:
  - show_all_identities.py
  - verify_index_usage.py → verify_identity_index.py
  - analyze_jewish_volume.py

### Performance Improvements

#### Detection Efficiency
- Regex pre-screen reduces LLM calls by ~30%
- Batch processing: 20 chunks per LLM call
- Caching: Instant results for repeat processing
- Surname search: Parallel regex across all chunks

#### Search Performance
- Identity lookup: O(1) via index
- Combined results: < 150ms
- No performance degradation from larger index

### Statistics

#### Before v3.0
```
Terms indexed:        19,165
Chunk mappings:       566,744
Identity support:     None
```

#### After v3.0
```
Terms indexed:        19,299 (+134)
Chunk mappings:       605,097 (+38,353)
Identity types:       342
Surnames tracked:     2,262
Occurrences:          38,754
```

### Breaking Changes
None. System is fully backwards compatible.

### Bug Fixes
- Fixed identity augmentation in `build_index.py` (was looking for wrong data structure)
- Fixed chunk ID format conversion (integer → string)
- Fixed verification script comparison logic

### Known Issues
- Surname ambiguity: Common names (Smith, Brown) may cause false positives
- Single mentions: Individuals mentioned once may be missed
- Name changes: Married names, adoptions not fully tracked

### Migration Guide
No migration needed. Simply rebuild index:
```bash
python build_index.py
```

All existing queries work unchanged with enhanced results.

---

## [v2.0] - 2025-11-10: Endnote Integration

### Features
- Full endnote parsing and indexing
- Chunk-to-endnote mappings
- 14,094 endnotes tracked

### Files Added
- `lib/document_parser.py` - Enhanced with endnote support
- `data/endnotes.json`
- `data/chunk_to_endnotes.json`

---

## [v1.0] - 2025-11-08: Initial Release

### Features
- Document parsing (.docx)
- Text chunking (500/100 words)
- Term indexing (19,165 terms)
- Vector database (ChromaDB)
- LLM narrative generation
- Thunderclap framework implementation

### Core Files
- `build_index.py`
- `query.py`
- `lib/index_builder.py`
- `lib/query_engine.py`
- `lib/llm.py`
- `lib/prompts.py`

