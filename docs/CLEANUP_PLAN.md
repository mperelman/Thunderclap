# Cleanup & Improvement Plan

**Date**: 2025-01-22
**Status**: In Progress

## Completed ✅

### 1. Shared Utilities Created
- ✅ Created `lib/text_utils.py` with `split_into_sentences()` and `extract_phrases()`
- ✅ Added `STOP_WORDS` to `lib/constants.py`
- ✅ Removed .txt file creation from `create_deduplicated_term_files()`

### 2. Code Updates Started
- ✅ Updated `lib/index_builder.py` imports to use shared utilities
- ✅ Removed duplicate STOP_WORDS definition
- ✅ Updated some references to use shared functions

## In Progress 🔄

### 3. Remove Nested Function Definitions
- Need to remove remaining nested `split_into_sentences()` definitions
- Update all references to use imported version from `text_utils.py`

### 4. Update query_engine.py
- Replace duplicate sentence splitting with `text_utils.split_into_sentences()`
- Replace stop words definitions with `constants.STOP_WORDS`

## Pending 📋

### 5. Archive Organization
- Run `scripts/cleanup_archives.py` to organize archives
- Moves archives to `docs/archive/` structure:
  - `lib_code/` - Archived library code
  - `sessions/` - Archived session files
  - `tests/` - Archived test files

### 6. Remove Unused Files
- Run `scripts/remove_unused_txt_files.py` to remove 33K+ unused .txt files
- Keeps only `deduplicated_cache.json`

### 7. Update Remaining Files
- Update `lib/query_engine.py` to use shared utilities
- Update any other files with duplicate code

## How to Run Cleanup

### Step 1: Organize Archives
```bash
python scripts/cleanup_archives.py
```
This will:
- Show what will be moved
- Ask for confirmation
- Move archives to organized structure

### Step 2: Remove Unused Files
```bash
python scripts/remove_unused_txt_files.py
```
This will:
- Show how many .txt files will be removed
- Show space that will be freed
- Ask for confirmation
- Remove unused files

### Step 3: Complete Code Updates
- Finish removing nested function definitions
- Update all references to use shared utilities
- Test to ensure everything works

## Benefits

1. **Reduced Duplication**: Shared utilities eliminate 5+ duplicate implementations
2. **Better Organization**: Archives organized in one place
3. **Disk Space**: Removes 33K+ unused files (saves significant space)
4. **Maintainability**: Single source of truth for shared functions
5. **Consistency**: All code uses same utilities

## Notes

- Archives are preserved, just reorganized
- Only unused files are removed (JSON cache is kept)
- All changes are backward compatible
- Scripts ask for confirmation before making changes



