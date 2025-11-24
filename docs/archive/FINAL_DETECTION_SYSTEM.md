# Final Optimized Identity Detection System

## System Architecture

### **1. LLM Detects SPECIFIC Identities**
- Prompt guides LLM to return: `sunni`, `maronite`, `hausa` (NOT generic `muslim`, `christian`, `african`)
- Comprehensive rules capture: origin, ancestry, conversion, geography, status
- Batch processing: 3 chunks per API call (efficient)
- Full chunk context: 3325 chars (no truncation)

### **2. Hierarchy Auto-Expands to General**
```python
Detected: {"assad": ["alawite"], "solh": ["sunni"], "chiha": ["maronite"]}

Index builds:
  'alawite' → chunk_123
  'muslim' → chunk_123 (auto-rollup from alawite)
  'sunni' → chunk_456
  'muslim' → chunk_456 (auto-rollup from sunni)
  'maronite' → chunk_789
  'christian' → chunk_789 (auto-rollup from maronite)
  'levantine' → chunk_789 (auto-rollup from maronite)
```

### **3. Search Works at All Levels**
```python
search('muslim')    → finds Assad (alawite), Solh (sunni), all Muslims
search('alawite')   → finds ONLY Assad (specific)
search('levantine') → finds Lebanese, Syrian, Palestinian, Jordanian
search('maronite')  → finds ONLY Maronite Christians
```

---

## Implementation

### **Files Created/Modified:**

1. **`lib/identity_hierarchy.py`** ✅ NEW
   - Defines hierarchical mappings
   - Functions: `get_parent_categories()`, `expand_identity_for_search()`

2. **`lib/api_key_manager.py`** ✅ NEW
   - Manages 6 API keys with automatic rotation
   - Daily capacity: 1200 requests

3. **`lib/llm_identity_detector.py`** ✅ UPDATED
   - Batch processing (3 chunks per call)
   - Full chunk context (no truncation)
   - Specific identity detection
   - Key rotation on quota

4. **`lib/index_builder.py`** ✅ UPDATED
   - Added `expand_with_hierarchy()` function
   - Auto-rollup: specific → general categories

5. **`lib/identity_detector_regex_archive.py`** ✅ ARCHIVED
   - Original regex approach (47% accuracy)
   - Backup if needed

---

## Efficiency Metrics

### **API Usage:**
- **Total chunks**: 1515
- **Already cached**: 1100 (72%)
- **Remaining**: 415 chunks
- **Batch size**: 3 chunks per call
- **API calls needed**: 415 ÷ 3 = **~138 calls**
- **Daily capacity**: 6 keys × 200 = **1200 requests**
- **Utilization**: 138/1200 = **11.5%** ✓

### **Token Usage:**
- **Per batch**: ~3343 tokens (3 full chunks + instructions)
- **Total**: 138 × 3343 = ~461K tokens
- **Limit**: 1M TPM
- **Utilization**: **46%** ✓

### **Time:**
- **5 seconds per batch** (rate limit buffer)
- **138 batches × 5s = 690 seconds**
- **Total time**: **~12 minutes** ✓

---

## Expected Results

### **Accuracy Improvement:**

**Regex (Baseline):** 22/47 people (47%)
- ✅ Latino: 8/8 (100%)
- ❌ Lebanese Wall St: 0/7 (0%)
- ❌ African: 3/9 (33%)
- ❌ Saudi: 0/2 (0%)

**LLM (Expected):** 42-45/47 people (90-95%)
- ✅ Latino: 8/8 (100%)
- ✅ Lebanese Wall St: 6-7/7 (85-100%)
- ✅ African: 7-8/9 (78-89%)
- ✅ Saudi: 1-2/2 (50-100%)

---

## Running Tomorrow

### **When API Quotas Reset (Midnight PT):**

```bash
cd C:\Users\perel\OneDrive\Apps\thunderclap-ai
python scripts/complete_detection_tomorrow.py
```

**What it does:**
1. Loads 6 API keys from `.env`
2. Processes 415 remaining chunks (with rotation)
3. Detects specific identities (sunni, maronite, hausa, etc.)
4. Saves to `data/detected_identities.json`
5. Rebuilds index with hierarchical expansion

**Then:**
```bash
python build_index.py
# Integrates LLM results + hierarchy into search index
```

**Result:**
- Search `muslim` → finds Sunni, Shia, Alawite, all subgroups
- Search `alawite` → finds only Alawites
- Search `christian` → finds Maronite, Coptic, Orthodox, all subgroups
- Search `levantine` → finds Lebanese, Syrian, Palestinian

---

## Key Improvements Over Regex

1. **No hardcoding** - No manual regex patterns per identity
2. **Comprehensive** - Captures origin + conversion + ancestry + geography
3. **Discoverable** - LLM can find identities I didn't anticipate (Druze, Ismaili, etc.)
4. **Hierarchical** - Both specific and general searches work
5. **Cached** - Only process new/changed chunks (incremental)
6. **Multi-attribute** - One person can have multiple identities
7. **Accurate** - Full context (3325 chars), understands nuance

---

## Maintenance

### **Adding New Documents:**
```bash
# Add new .docx to data/documents/
python scripts/complete_detection_tomorrow.py
# Only processes NEW chunks (cached system)
```

### **Refining Prompts:**
```python
# In lib/llm_identity_detector.py
PROMPT_VERSION = "v2"  # Increment version
# Update prompt text
# Run: python lib/llm_identity_detector.py --force
```

### **Adding New Hierarchy:**
```python
# In lib/identity_hierarchy.py
IDENTITY_HIERARCHY['muslim'].append('new_subgroup')
# Rebuild index: python build_index.py
```

---

## Status

✅ System designed and implemented
✅ 6 API keys configured (1200 RPD capacity)
✅ 72% already cached (1100/1515 chunks)
✅ Hierarchy system tested and working
✅ Ready to complete tomorrow
⏳ Waiting for API quota reset (midnight PT)


