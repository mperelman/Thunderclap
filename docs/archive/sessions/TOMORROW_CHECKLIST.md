# Tomorrow's Checklist - Complete Identity Detection

**When:** After midnight Pacific Time (API quotas reset)  
**Time needed:** ~12 minutes  
**Expected result:** 90-95% accuracy (vs current 47%)

---

## ✅ What's Ready

- ✅ 6 API keys configured (1200 requests/day capacity)
- ✅ 72% already cached (1100/1515 chunks processed)
- ✅ LLM detector with batch processing (efficient)
- ✅ Hierarchy system (specific → general indexing)
- ✅ Multi-attribute support (Chavez: sephardi + basque + latino)
- ✅ Full chunk context (no truncation)

---

## 📋 Steps to Run

### **Step 1: Complete LLM Detection**
```bash
python scripts/complete_detection_tomorrow.py
```

**What it does:**
- Processes remaining 415 chunks
- Uses 6 API keys with automatic rotation
- ~138 API calls (11.5% of daily capacity)
- ~12 minutes
- Saves to `data/detected_identities.json`

**Expected output:**
```
[COMPLETE]
  Total chunks: 1515
  Cache hits: 1100
  New chunks processed: 415
  API calls made: 138
  
Identities detected: ~50
Lebanese detected: [abdelnour, boutros, chammah, bitar, jabre, mack, ...]
Black detected: [dantata, okwei, ogunlesi, thiam, ouattara, ...]
```

---

### **Step 2: Rebuild Index**
```bash
python build_index.py
```

**What it does:**
- Integrates LLM results into search index
- Applies hierarchical expansion (alawite → muslim)
- Makes all identities searchable

**Expected output:**
```
Step 3c: Augmenting indices with identity metadata...
  [OK] Added ~30000 identity→chunk links
  [OK] Added ~5000 hierarchical links (specific->general)
```

---

### **Step 3: Verify Results**

```bash
# Check detection coverage
python -c "
import json
d = json.load(open('data/detected_identities.json'))

print('Identities detected:', len(d['identities']))

# Check key identities
for identity in ['lebanese', 'latino', 'black', 'muslim', 'hausa']:
    data = d['identities'].get(identity, {})
    families = data.get('families', []) or data.get('individuals', [])
    print(f'{identity}: {len(families)} families - {families[:8]}')"
```

**Expected:**
- Lebanese: ~20 families (including Wall St: Abdelnour, Boutros, Chammah, etc.)
- Latino: ~8 individuals (Alvarez, Chavez, Diaz, etc.)
- Black: ~15+ (Dantata, Okwei, Ogunlesi, Thiam, etc.)
- Muslim: Specific subgroups detected (will check)

---

### **Step 4: Test Hierarchical Search**

```bash
# Test hierarchy works
python -c "
from lib.search_engine import SearchEngine
s = SearchEngine()

# General searches
print('muslim bankers:', len(s.keyword_search('muslim', 10)), 'chunks')
print('christian bankers:', len(s.keyword_search('christian', 10)), 'chunks')
print('levantine bankers:', len(s.keyword_search('levantine', 10)), 'chunks')

# Specific searches
print('alawite bankers:', len(s.keyword_search('alawite', 10)), 'chunks')
print('maronite bankers:', len(s.keyword_search('maronite', 10)), 'chunks')
print('hausa bankers:', len(s.keyword_search('hausa', 10)), 'chunks')"
```

**Expected:** Both general and specific searches return results

---

### **Step 5: Test Multi-Attribute**

```bash
# Verify Chavez appears in multiple categories
python -c "
from lib.search_engine import SearchEngine
s = SearchEngine()

searches = ['jewish', 'sephardi', 'basque', 'latino', 'hispanic']
for term in searches:
    results = s.keyword_search(term, 50)
    print(f'{term}: {len(results)} chunks')
    # Check if any contain 'chavez'
"
```

**Expected:** Chavez appears in jewish (via sephardi), sephardi, basque, latino searches

---

## 🎯 Success Criteria

**Must have:**
- ✅ >85% accuracy (40/47 known people detected)
- ✅ Wall St Lebanese found (Abdelnour, Boutros, Chammah, Bitar, Jabre)
- ✅ African bankers found (Dantata, Okwei, Ogunlesi, Thiam)
- ✅ No crashes or errors

**Nice to have:**
- ✅ >90% accuracy (42+ people)
- ✅ Multi-attribute working (Chavez in multiple categories)
- ✅ Hierarchy working (muslim finds all subgroups)
- ✅ New identities discovered (Druze, Ismaili, etc.)

---

## 🔧 If Issues Occur

### **If accuracy < 85%:**
1. Check `data/llm_identity_cache.json` - inspect LLM responses
2. Refine prompt in `lib/llm_identity_detector.py`
3. Increment `PROMPT_VERSION = "v2"`
4. Run with `--force` flag

### **If API errors:**
1. Check key rotation is working
2. Verify all 6 keys in `.env`
3. Wait for quota reset (midnight PT)

### **If want to revert to regex:**
```bash
# In build_index.py line ~59:
from lib.identity_detector import detect_identities_from_index
# (Already points to regex version)

python build_index.py
```

---

## 📊 Expected Final Results

**People Found:** 42-45 out of 47 (90-95%)

**Categories Detected:** ~50-60 identities including:
- Religious: jewish, muslim (sunni, shia, alawite), christian (maronite, coptic, orthodox)
- Ethnic: lebanese, palestinian, armenian, greek, basque, hausa, yoruba, igbo
- Racial: black, white
- Gender: female (with royal titles)
- Status: converted, royal

**Search Capability:**
- General: "muslim bankers" finds ALL Muslim subgroups
- Specific: "alawite bankers" finds only Alawites
- Multi-level: "levantine bankers" finds Lebanese + Syrian + Palestinian
- Multi-attribute: Chavez findable via jewish/sephardi/basque/latino

---

## 📝 Notes

- LLM cache persists across runs (incremental updates efficient)
- Only process new/changed chunks in future
- Prompt refinement doesn't require rebuilding from scratch
- System discovers new identities automatically (no hardcoding)

---

**See `IDENTITY_DETECTION_STATUS.md` for complete system documentation**


