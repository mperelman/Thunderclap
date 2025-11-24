# Final 4-Step Identity Detection Architecture

## The Complete Flow (Your Design)

### STEP 1: Regex Prescreen (Fast, Free)
**Purpose:** Identify chunks with identity keywords

**Input:** 1,517 total chunks  
**Process:** Search for keywords: black, hausa, jewish, sephardi, gay, homosexual, etc.  
**Output:** 1,292 chunks with keywords (85%)  
**Savings:** Skip 225 chunks (15%) - no LLM processing needed

**File:** `lib/identity_prefilter.py`  
**API calls:** 0

---

### STEP 2: LLM Extraction (Only on relevant chunks)
**Purpose:** Extract surnames + their specific identities

**Input:** 1,292 chunks from Step 1  
**Process:** Send to LLM with full context  
**Output:** `{"rothschild": ["jewish", "ashkenazi"], "dantata": ["hausa"], "parsons": ["black"]}`  
**Result:** ~200-300 unique surnames with identities

**File:** `lib/llm_identity_detector.py` (with pre-filter integrated)  
**API calls:** ~65 batches (was 76 without pre-filter)

**Example:**
```
Chunk: "Jewish Rothschild and Sephardi Sassoon traded in London..."

LLM returns:
{
  "rothschild": ["jewish", "ashkenazi"],
  "sassoon": ["jewish", "sephardi"]
}
```

---

### STEP 3: Surname Search (Find ALL mentions)
**Purpose:** Find EVERY chunk containing those surnames (even without identity keywords)

**Input:** 
- Surnames from Step 2: {Rothschild, Sassoon, Parsons, Dantata, ...}
- ALL 1,517 chunks

**Process:** Regex search each chunk for each surname  
**Output:** Chunk IDs for each surname

**Example:**
```
Search "Rothschild" in all 1,517 chunks:
  Chunk 52: "Jewish Rothschild founded..." ← HAS keyword
  Chunk 103: "Rothschild merged with Baring..." ← NO keyword!
  Chunk 447: "Rothschild family expanded..." ← NO keyword!
  
Result: "Rothschild" → [52, 103, 447, ...]
```

**File:** New regex search in `lib/identity_detector_v3.py`  
**API calls:** 0 (pure regex)

---

### STEP 4: Index Integration (Add to search index)
**Purpose:** Make identities searchable

**Input:** 
- Surname → identities: `{"rothschild": ["jewish", "ashkenazi"]}`
- Surname → chunks: `{"rothschild": [52, 103, 447, ...]}`

**Process:** Map identities to chunks via surnames + hierarchy  
**Output:** Index entries

**Example:**
```
Identity: "ashkenazi"
  → Chunks: [52, 103, 447] (Rothschild chunks)
  
Identity: "jewish" (via hierarchy: ashkenazi → jewish)
  → Chunks: [52, 103, 447] (Rothschild) + [89, 201] (Sassoon) + ...
  
Identity: "black"
  → Chunks: [12, 44] (Parsons) + [78, 91] (Dantata via hausa→black)
```

**File:** `lib/index_builder.py` (existing `augment_indices_with_identities`)  
**API calls:** 0

---

## Complete Example: "Black Bankers"

### Chunks in Documents:
```
Chunk 12: "Black banker Richard Parsons joined Citi..." ← Says "black"
Chunk 44: "Parsons became Chair..." ← NO keyword, just surname
Chunk 78: "Hausa Dantata dominated Nigerian trade..." ← Says "hausa"
Chunk 91: "Dantata deposited silver..." ← NO keyword, just surname
```

### Step 1: Prescreen
```
Chunk 12: "black" found → PASS
Chunk 44: No keywords → SKIP (for now)
Chunk 78: "hausa" found → PASS
Chunk 91: No keywords → SKIP (for now)
```

### Step 2: LLM Extraction (on chunks 12, 78)
```
Chunk 12 → {"parsons": ["black", "african_american"]}
Chunk 78 → {"dantata": ["hausa", "nigerian"]}
```

### Step 3: Surname Search (ALL chunks)
```
Search "Parsons": Found in chunks [12, 44]
Search "Dantata": Found in chunks [78, 91]
```

### Step 4: Index
```
"black" → chunks [12, 44, 78, 91]
  - Parsons (direct: black)
  - Dantata (via: hausa → black hierarchy)

"hausa" → chunks [78, 91] (specific)
"nigerian" → chunks [78, 91] (specific)
```

### Final Result:
**Search "black bankers"** → Returns chunks [12, 44, 78, 91]
- Includes Parsons (explicitly black)
- Includes Dantata (hausa → black via hierarchy)
- Includes ALL mentions of both surnames (even without keywords!)

---

## API Efficiency

### Without this approach:
- Process: All 1,517 chunks
- API calls: 76 batches
- Misses: Chunks without keywords (Chunk 44, 91)

### With 4-step approach:
- Process: 1,292 chunks (15% reduction)
- API calls: 65 batches (15% savings)
- Finds: ALL surname mentions (Chunks 44, 91 included!)

**Win-win: Fewer API calls + more complete results**

---

## Handling False Positives

**Example: Eugene Black (white banker)**
- Step 2: LLM might extract `{"black": ["surname"]}` (if sees "Eugene Black")
- Step 3: Finds all "Black" surname chunks
- Step 4: Indexes under "black" identity

**Result:** Eugene Black shows up in "black bankers" search

**Solution:** Narrative LLM filters this during generation:
- Reads: "Eugene Black, white banker..."
- Narrative: Excludes him from black bankers section
- Acceptable false positive

**Your quote:** "that can possibly be handled during the narrative llm step" ✓

---

## Ready for 3am

**Current status:**
- ✅ Pre-filter working (tested, 15% savings)
- ✅ V3 architecture built
- ✅ Surname search logic ready
- ❌ Needs quota to run Step 2 (LLM extraction)

**At 3am:** Run this and it will work properly with all 4 steps!


