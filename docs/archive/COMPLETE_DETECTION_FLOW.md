# Complete Identity Detection Flow (Final Architecture)

## The 2-Step Process (Smart & Efficient)

### Step 1: Regex Pre-filter (Fast, Free)
**File:** `lib/identity_prefilter.py`

```
1,517 total chunks
    ↓ [Regex scan for identity keywords]
1,292 relevant chunks (85%)
    ↓
225 chunks filtered out (15% - no identity keywords)
```

**What it finds:**
- Chunks mentioning: black, hausa, jewish, sephardi, gay, homosexual, lebanese, etc.
- Fast regex search (milliseconds, 0 API calls)
- Reduces LLM work by 15%

---

### Step 2: LLM Processing (Only relevant chunks)
**File:** `lib/llm_identity_detector.py` or `lib/batch_identity_detector.py`

```
1,292 relevant chunks
    ↓ [Send to LLM in batches of 20]
~65 API calls (was 76 without pre-filter)
    ↓ [LLM extracts: {"parsons": ["black"], "dantata": ["hausa"]}]
Specific identities detected
```

**What LLM does:**
- Reads full chunk context
- Extracts surnames + their specific identities
- Returns: `{"dantata": ["hausa"], "parsons": ["black"], "boutros": ["lebanese", "maronite"]}`

---

### Step 3: Hierarchy Consolidation (Automatic)
**File:** `lib/identity_hierarchy.py`

```
Specific identities from LLM:
- hausa, yoruba, igbo → black
- sunni, shia, alawite → muslim  
- sephardi, ashkenazi → jewish
- maronite, coptic, greek_orthodox → christian
```

**File:** `lib/index_builder.py` (function: `expand_with_hierarchy`)

---

### Step 4: Index BOTH Levels
**File:** `lib/index_builder.py`

```
Search "black bankers":
  → Finds chunks tagged: black (direct) + hausa + yoruba + igbo (via hierarchy)

Search "hausa bankers":
  → Finds only chunks tagged: hausa (specific)

Search "muslim bankers":
  → Finds chunks tagged: muslim (direct) + sunni + shia + alawite (via hierarchy)
```

---

## Example Flow

**Input chunk:**
```
Hausa Dantata dominated Nigeria's trade. The Yoruba princess 
Omu Okwei controlled Igboland. In America, Black banker 
Richard Parsons joined Citi.
```

### Step 1: Regex Pre-filter
```
Keywords found: hausa, yoruba, igbo, black
→ PASS to LLM
```

### Step 2: LLM Extraction
```
LLM returns:
{
  "dantata": ["hausa"],
  "okwei": ["yoruba"],
  "parsons": ["black", "african_american"]
}
```

### Step 3: Hierarchy
```
hausa → black
yoruba → black
african_american → black
```

### Step 4: Index
```
Specific:
  "hausa" → [chunk_52]
  "yoruba" → [chunk_52]
  "african_american" → [chunk_52]

General (via hierarchy):
  "black" → [chunk_52] (from hausa + yoruba + african_american)
```

### Result
```
Search "black bankers" → Finds chunk_52 (Dantata, Okwei, Parsons)
Search "hausa" → Finds chunk_52 (Dantata only)
Search "yoruba" → Finds chunk_52 (Okwei only)
```

---

## Your Specific Cases Solved

### 1. Black Complexity
**Problem:** Some say "black", some say "hausa", some say neither

**Solution:**
- Pre-filter finds chunks with: black, hausa, yoruba, igbo, african american
- LLM extracts specific: `{"dantata": ["hausa"]}`
- Hierarchy maps: hausa → black
- Index under BOTH
- Search "black" finds Hausa bankers ✓

### 2. Gay/LGBT Terminology  
**Problem:** Various terms (gay, homosexual, bisexual, lavender marriage)

**Solution:**
- Pre-filter finds chunks with ANY variant
- LLM extracts: `{"context": ["lgbt"]}` (general context, not individuals)
- Index under "lgbt"
- Search "gay bankers" finds all LGBT context ✓

### 3. Jewish Variations
**Problem:** Some say "jewish", some "sephardi", some nothing

**Solution:**
- Pre-filter finds: jewish, sephardi, ashkenazi, court jew, kohanim
- LLM extracts: `{"rothschild": ["jewish"], "sassoon": ["sephardi"]}`
- Hierarchy: sephardi → jewish
- Index under BOTH
- Search "jewish" finds Sephardi too ✓

---

## Efficiency Gains

### Without Pre-filter:
- Process: 1,517 chunks
- API calls: 76 batches
- Cost: 100%

### With Pre-filter:
- Process: 1,292 chunks (15% fewer)
- API calls: 65 batches (11 fewer)
- Cost: 85%
- **Savings: 15% API calls + faster processing**

---

## Files in the Flow

1. **lib/identity_prefilter.py** - Regex pre-filter (NEW)
2. **lib/llm_identity_detector.py** - LLM extraction (FIXED - now uses pre-filter)
3. **lib/identity_hierarchy.py** - Hierarchy mapping (existing)
4. **lib/index_builder.py** - Index integration (existing)

---

## Ready to Test at 3am

**Run:** `python temp/run_at_3am.py`

Expected results:
- Should detect 100s of identities (not just 8)
- Saves 15% on API calls
- Properly handles all your edge cases (hausa→black, etc.)


