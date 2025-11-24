# Identity Detection System - Current Status

**Date:** November 11, 2025  
**Status:** Ready for final LLM detection run tomorrow

---

## Quick Start (Tomorrow After Midnight PT)

```bash
# 1. Run LLM detection (completes in ~12 minutes)
python scripts/complete_detection_tomorrow.py

# 2. Rebuild search index with results
python build_index.py

# 3. Test
python query.py "tell me about lebanese bankers"
```

---

## Current System

### **Active Detection: Regex (Temporary)**
- File: `lib/identity_detector.py`
- Accuracy: 47% (22/47 known people)
- Used by: `build_index.py`
- **Will be replaced tomorrow**

### **New Detection: LLM (Ready to Deploy)**
- File: `lib/llm_identity_detector.py`
- Expected accuracy: 90-95%
- Batch processing: 3 chunks per API call
- Multi-attribute + hierarchical
- **Deploys tomorrow after API quota resets**

---

## Folder Structure

```
thunderclap-ai/
├── data/
│   ├── documents/              # Source .docx files
│   ├── cache/                  # Parsed .docx cache
│   ├── indices.json            # Search index
│   ├── detected_identities.json # LLM detection results
│   └── llm_identity_cache.json  # LLM chunk cache (1100/1515 done)
│
├── lib/
│   ├── llm_identity_detector.py ⭐ NEW - LLM detection
│   ├── api_key_manager.py       ⭐ NEW - 6-key rotation
│   ├── identity_hierarchy.py    ⭐ NEW - Hierarchical indexing
│   ├── identity_detector.py     📋 CURRENT - Regex (47%)
│   ├── archived/                # Old approaches
│   │   ├── identity_detector_regex_archive.py
│   │   └── identity_detector_fast.py
│   ├── query_engine.py          # Query orchestration
│   ├── search_engine.py         # Vector + keyword search
│   ├── index_builder.py         # Index building
│   ├── prompts.py               # LLM prompts
│   ├── identitys.py           # Hardcoded families
│   └── README.md                # Module documentation
│
├── scripts/
│   ├── complete_detection_tomorrow.py ⭐ RUN TOMORROW
│   └── analyze_attributes.py
│
├── tests/
│   ├── run_experiments.py       # Compare detection approaches
│   ├── test_llm_on_sample.py    # Test LLM on 10 chunks
│   └── README.md
│
├── docs/
│   ├── FINAL_DETECTION_SYSTEM.md     # Complete system docs
│   ├── IDENTITY_DETECTION_EXPERIMENTS.md
│   ├── THUNDERCLAP_GUIDE.md
│   └── ... (other docs)
│
├── .env                         # 6 API keys configured
├── build_index.py               # Build search index
├── query.py                     # Query interface
└── requirements.txt
```

---

## What Changed Today

### **Created:**
1. ✅ `lib/llm_identity_detector.py` - Efficient LLM-based detection
2. ✅ `lib/api_key_manager.py` - 6-key rotation (1200 RPD capacity)
3. ✅ `lib/identity_hierarchy.py` - Hierarchical specific→general mapping
4. ✅ `scripts/complete_detection_tomorrow.py` - Auto-run script
5. ✅ `tests/` folder - Organized test scripts
6. ✅ `lib/archived/` folder - Old approaches

### **Modified:**
1. ✅ `lib/index_builder.py` - Added hierarchy expansion
2. ✅ `.env` - Configured 6 API keys
3. ✅ Multiple documentation files

### **Archived:**
1. ✅ Regex detector backed up (can revert if needed)
2. ✅ Old fast detector archived

---

## System Comparison

### **Regex Approach (Current, Temporary)**
| Metric | Value |
|--------|-------|
| Accuracy | 47% (22/47 people) |
| API Calls | 0 |
| Maintenance | High (100+ patterns) |
| Extensibility | Low (manual patterns) |
| Multi-attribute | Limited |

### **LLM Approach (Tomorrow)**
| Metric | Value |
|--------|-------|
| Accuracy | 90-95% (expected) |
| API Calls | 138 (batched) |
| Maintenance | Low (prompt-based) |
| Extensibility | High (discovers new) |
| Multi-attribute | Full support |

---

## API Quota Status

**6 API Keys Configured:**
- Key #1-6: All exhausted today (resets midnight PT)
- Daily capacity: 6 × 200 = **1200 requests/day**
- Tomorrow needed: **138 requests** (11.5% of capacity)

**Cached Progress:**
- 1100/1515 chunks already processed (72%)
- Only 415 chunks remaining
- Will complete in ~12 minutes tomorrow

---

## Tomorrow's Workflow

### **Step 1: Complete Detection**
```bash
python scripts/complete_detection_tomorrow.py
```
**Output:** `data/detected_identities.json` with ~45/47 people

### **Step 2: Rebuild Index**
```bash
python build_index.py
```
**Integrates:** LLM results + hierarchical expansion

### **Step 3: Test**
```bash
# Test hierarchical search
python -c "from lib.search_engine import SearchEngine; s = SearchEngine(); 
print('Muslim:', len(s.keyword_search('muslim', 10)));
print('Alawite:', len(s.keyword_search('alawite', 10)));
print('Christian:', len(s.keyword_search('christian', 10)));
print('Maronite:', len(s.keyword_search('maronite', 10)))"
```

### **Step 4: Verify Results**
```bash
python -c "import json; d = json.load(open('data/detected_identities.json'));
print('Identities:', len(d['identities']));
print('Lebanese:', d['identities']['lebanese']['families'][:10]);
print('Black:', d['identities']['black'].get('families', [])[:10])"
```

### **Step 5: If Good, Update build_index.py**
Replace regex with LLM detector:
```python
# In build_index.py, line ~59:
# OLD:
from lib.identity_detector import detect_identities_from_index

# NEW:
from lib.llm_identity_detector import detect_identities_from_index
```

---

## Cleanup Needed (Optional)

If LLM detection works well:

1. **Delete:** `lib/identity_detector.py` (duplicate of archive)
2. **Update:** `build_index.py` to use LLM detector
3. **Keep:** `lib/archived/` as backup (just in case)

---

## Key Improvements

1. **Efficiency**: 91% fewer API calls (batching)
2. **Accuracy**: 47% → 90%+ expected (comprehensive LLM)
3. **Maintainability**: No regex patterns to maintain
4. **Discoverability**: Finds new identities (Druze, Ismaili, etc.)
5. **Hierarchical**: Searches work at specific + general levels
6. **Multi-attribute**: Chavez = sephardi + basque + latino (all searchable)
7. **Scalable**: Add new documents, only process new chunks

---

## Success Metrics (Tomorrow)

**Minimum Success:**
- ✅ >85% accuracy (40/47 people)
- ✅ <10% false positives
- ✅ Completes without errors

**Ideal Success:**
- ✅ >90% accuracy (42+ people)
- ✅ <5% false positives
- ✅ Multi-attribute working (Chavez in multiple categories)
- ✅ Hierarchy working (muslim finds all subgroups)

---

## Support

See detailed documentation:
- `docs/FINAL_DETECTION_SYSTEM.md` - Complete system architecture
- `docs/IDENTITY_DETECTION_EXPERIMENTS.md` - Experiment designs
- `lib/README.md` - Module descriptions
- `tests/README.md` - Test script usage


