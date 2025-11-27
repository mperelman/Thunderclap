# Code Audit Report - November 26, 2024

## Summary
- **Archived**: 81 temporary files from `temp/` directory → `temp/archived_temp_20251126_212719/`
- **Main Entry Points**: `query.py`, `server.py`, `build_index.py`
- **Core Library**: `lib/` directory with 25 modules

## Archived Files
All temporary test/debug scripts have been moved to `temp/archived_temp_20251126_212719/`

## Core Application Structure

### Main Entry Points
1. **query.py** - CLI interface for querying
   - Imports: `lib.query_engine.QueryEngine`
   
2. **server.py** - FastAPI web server
   - Imports: `lib.query_engine.QueryEngine`, `lib.config.MAX_ANSWER_LENGTH`
   
3. **build_index.py** - Index building script
   - Imports: `lib.document_parser`, `lib.index_builder`, `lib.config`

### Core Library Modules (lib/)

**Actively Used (Verified):**
- ✅ `query_engine.py` - Main query orchestration (imported by query.py, server.py)
- ✅ `index_builder.py` - Index building (imported by build_index.py)
- ✅ `document_parser.py` - Document parsing (imported by build_index.py)
- ✅ `config.py` - Configuration (imported by all entry points)
- ✅ `llm.py` - LLM wrapper (imported by query_engine.py)
- ✅ `prompts.py` - Prompt templates (imported by query_engine.py)
- ✅ `batch_processor_iterative.py` - Batch processing (imported by query_engine.py)
- ✅ `batch_processor_geographic.py` - Geographic processing (imported by query_engine.py)
- ✅ `answer_reviewer.py` - Answer review (imported by query_engine.py)
- ✅ `engines/` - Specialized engines (imported by query_engine.py)
  - `market_engine.py`
  - `ideology_engine.py`
  - `event_engine.py`
  - `period_engine.py`
- ✅ `acronyms.py` - Acronym expansions (imported by query_engine.py, index_builder.py)
- ✅ `economic_systems.py` - Economic system definitions (imported by ideology_engine.py)
- ✅ `term_utils.py` - Term utilities (imported by query_engine.py, index_builder.py)
- ✅ `text_utils.py` - Text utilities (imported by query_engine.py, index_builder.py)
- ✅ `constants.py` - Constants (imported by query_engine.py, index_builder.py)
- ✅ `identity_hierarchy.py` - Identity hierarchy (imported by index_builder.py, scripts)

**Used by Scripts Only:**
- ⚠️ `llm_identity_detector.py` - Used by identity detection scripts, not main app
- ⚠️ `identity_prefilter.py` - Used by identity detection scripts
- ⚠️ `panic_indexer.py` - May be used by scripts

**Archived (Confirmed Unused):**
- ✅ `deduplicate_index.py` - Post-indexing deduplication utility - not imported anywhere → Archived to `docs/archive/lib_code/archived_unused_20251126/`
- ✅ `identity_detector_v3.py` - Identity detector v3 - not imported anywhere → Archived to `docs/archive/lib_code/archived_unused_20251126/`

**Restored (Actually Used):**
- ✅ `identity_terms.py` - Identity terms list - **RESTORED** - Actually imported by `query_engine.py` in 3 places (firm name detection, control/influence queries, broad identity queries)

### Scripts Directory

**Active Scripts (Keep):**
- ✅ `run_identity_detection.py` - Identity detection workflow
- ✅ `run_batch_detection.py` - Batch identity detection
- ✅ `check_batch_status.py` - Check batch job status
- ✅ `verify_identity_index.py` - Verify identity indexing
- ✅ `show_all_identities.py` - Display all identities
- ✅ `analyze_jewish_volume.py` - Analysis utility
- ✅ `analyze_attributes.py` - Analysis utility

**Maintenance Scripts (Keep):**
- ✅ `cleanup_archives.py` - Archive cleanup
- ✅ `remove_unused_txt_files.py` - File cleanup
- ✅ `deploy.py` - Deployment script

**Potentially Obsolete:**
- ❓ `add_panic_indexing_simple.py` - May be integrated into build_index.py

## Recommendations

### High Priority
1. **Verify `deduplicate_index.py`**: Not imported anywhere - check if deduplication is handled elsewhere
2. **Verify `identity_terms.py`**: Not imported anywhere - may be legacy code
3. **Verify `identity_detector_v3.py`**: Not imported - may be superseded by `llm_identity_detector.py`

### Medium Priority
4. **Review `add_panic_indexing_simple.py`**: If panic indexing is integrated into build_index.py, archive this script
5. **Consolidate identity detection**: Review if multiple identity detector files are needed

### Low Priority
6. **Archive old session files**: `temp/archived_session_20250121/` can be moved to `docs/archive/` if not needed

## Files Already Archived
- ✅ All temp/ test scripts → `temp/archived_temp_20251126_212719/`
- ✅ Old archived code → `docs/archive/`

## Next Steps
1. Review the three potentially unused modules (`deduplicate_index.py`, `identity_terms.py`, `identity_detector_v3.py`)
2. If confirmed unused, move to `docs/archive/lib_code/archived/`
3. Update this document with findings

