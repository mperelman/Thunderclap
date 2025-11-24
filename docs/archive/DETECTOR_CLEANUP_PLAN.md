# Detector Cleanup Plan

## Your 3 Detectors (What You Want)

### 1. Archived Regex Detector
**Location:** `lib/archived/identity_detector_regex_archive.py`
**Status:** ✅ Already archived
**Purpose:** Historical reference, 47% accuracy

### 2. Batch LLM Detector (TEST FIRST)
**Location:** `lib/batch_identity_detector.py`
**Status:** ✅ Ready
**Purpose:** 50% cost, async processing, no quota limits
**Command:** `python scripts/run_batch_detection.py`

### 3. Sequential LLM Detector (TEST AFTER)
**Location:** `lib/llm_identity_detector.py`
**Status:** ✅ Just fixed (v2)
**Purpose:** Real-time processing, uses key rotation
**Command:** `python lib/llm_identity_detector.py`

---

## Current Detector Files (Actual Status)

**Active:**
- `lib/identity_detector.py` ← OLD regex (build_index.py imports this!) ❌ DELETE
- `lib/llm_identity_detector.py` ← Sequential LLM ✅ KEEP
- `lib/batch_identity_detector.py` ← Batch LLM ✅ KEEP
- `lib/identity_hierarchy.py` ← Support file for hierarchical indexing ✅ KEEP
- `lib/api_key_manager.py` ← Key rotation ✅ KEEP

**Archived:**
- `lib/archived/identity_detector_regex_archive.py` ✅ KEEP
- `lib/archived/identity_detector_fast.py` ❌ DELETE (duplicate)

---

## All Other Files - What They Do

### CORE SYSTEM (Keep - These make it work):
- `query.py` - Main entry point
- `build_index.py` - Builds search index
- `lib/query_engine.py` - Query orchestration
- `lib/search_engine.py` - Search logic
- `lib/index_builder.py` - Index building
- `lib/document_parser.py` - Parse Word docs
- `lib/batch_processor.py` - LLM batch processing
- `lib/llm.py` - LLM API wrapper
- `lib/prompts.py` - Narrative prompts
- `lib/config.py` - Configuration

### SCRIPTS (Keep - User commands):
- `scripts/run_batch_detection.py` - Run batch detector
- `scripts/check_batch_status.py` - Check batch status

### SCRIPTS (Delete - Obsolete):
- `scripts/complete_detection_tomorrow.py` - Old approach
- `scripts/auto_run_when_ready.py` - Old approach
- `scripts/safe_incremental_test.py` - Test (move to tests/)
- `scripts/analyze_attributes.py` - Utility (check if used)

### TEMP FILES (Delete - All test junk):
**18 test scripts in temp/:**
- test_all_keys.py
- test_api_enabled.py
- test_black_bankers.py
- test_fixed_extraction.py
- test_fixed_rotation.py
- test_fresh_key.py
- test_key_rotation.py
- test_new_key.py
- test_query_api.py
- find_detected_identities.py
- show_detected_identities.py
- show_real_detections.py
- list_batch_models.py
- investigate_detector_failure.py
... etc

**Keep in temp/:**
- panic_1837_result.txt - Actual output
- run_at_3am.py - Today's test script
- batch_requests.jsonl - Used by batch API

### DOCUMENTATION (Keep - Prevents my mistakes):
- README.md - Main guide
- docs/*.md - All documentation
- Root *.md files - Project status

---

## RECOMMENDED ACTIONS

### 1. Move Old Detector to Archive
```bash
Move-Item lib/identity_detector.py lib/archived/
```

### 2. Delete Duplicate Archive
```bash
Remove-Item lib/archived/identity_detector_fast.py
```

### 3. Clean Temp Folder
```bash
Remove-Item temp/test_*.py
Remove-Item temp/*_detections.py
Remove-Item temp/*_keys.py
Remove-Item temp/investigate_*.py
```

### 4. Clean Obsolete Scripts
```bash
Remove-Item scripts/complete_detection_tomorrow.py
Remove-Item scripts/auto_run_when_ready.py
```

---

## After Cleanup: 3 Detectors Only

1. **lib/archived/identity_detector_regex_archive.py** (historical)
2. **lib/batch_identity_detector.py** (test first at 3am)
3. **lib/llm_identity_detector.py** (test second at 3am)

**All other files support these or are core system.**

Execute cleanup now?


