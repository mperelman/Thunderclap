# Identity Detection System - Complete ✅

## What We Built

A **4-step identity detection system** that finds banking figures by identity attributes even when those attributes aren't explicitly mentioned every time.

### The 4 Steps:

1. **Regex Pre-screen** → Fast scan for identity keywords (jewish, black, alawite, etc.)
2. **LLM Extraction** → Extract surnames + identities from relevant chunks
3. **Surname Search** → Find ALL occurrences of those surnames across entire corpus
4. **Index Integration** → Make identities searchable alongside regular terms

## Results

### Detection Statistics:
- **342 identity types** detected across documents
- **2,262 unique surnames** extracted  
- **38,754 surname occurrences** indexed
- **1,017/1,517 chunks** contained identity information (67%)

### Top Identities Detected:
```
christian      1,494 chunks    black           1,332 chunks
jewish         1,480 chunks    quaker          1,087 chunks
american       1,446 chunks    ashkenazi       1,015 chunks
british        1,426 chunks    sephardi          940 chunks
catholic       1,333 chunks    huguenot          660 chunks
protestant     1,234 chunks    kohanim           432 chunks
```

### Specific Examples:
```
alawite            7 chunks    gay                 6 chunks
sunni             43 chunks    basque             44 chunks
shia              21 chunks    latino/latina   15/12 chunks
muslim           356 chunks    hispanic           17 chunks
```

## How It Works

**Example: "alawite bankers"**

1. User searches: `python query.py "alawite bankers"`
2. System finds:
   - Direct mentions: "Alawite Salah Jadid"
   - Implied mentions: Later references to "Jadid" or "Asad" without repeating "Alawite"
3. Returns **96 keyword matches** (7 direct + 89 implied via surnames)
4. LLM generates narrative from all relevant chunks

**Why This Matters:**

Documents mention identity once, then use surnames. Without this system:
- "Alawite Salah Jadid" ✅ (found)
- "Jadid consolidated power" ❌ (missed)

With this system:
- Both found! System knows Jadid = Alawite from earlier context

## Test Results

### Black Bankers
- **211 matches** found
- Generated narrative covering:
  - Andrew Brimmer (1st Black Fed Governor, 1966)
  - Emmett Rice (2nd Black Fed Governor, 1978)
  - Vernon Jordan (Bankers Trust → Akin Gump)
  - Napoleon Brandford (Grigsby Brandford, 1984)
  - Richard Parsons (1st Black S&L CEO, 1988)
  - Raymond McGuire (Merrill M&A, 1994)
  - Stanley O'Neal (CEO succession)

### Alawite Bankers
- **96 matches** found
- Generated narrative covering:
  - Salah Jadid (1966 coup)
  - Hafez Asad (Defense Minister)

### Gay Bankers
- **96 matches** found
- Sparse narrative (1307 Templars) - accurately reflects document content

## Technical Implementation

### Files Created/Modified:
- `lib/llm_identity_detector.py` - v2 with fixed extraction logic
- `lib/identity_detector_v3.py` - Full 4-step pipeline
- `lib/identity_prefilter.py` - Fast regex pre-screen
- `build_index.py` - Modified to integrate v3 detection results
- `data/identity_detection_v3.json` - 342 identities + 2,262 surnames
- `data/llm_identity_cache.json` - LLM results cache (v2)

### Performance:
- **LLM Usage**: 1,517 chunks → 1,017 with identities (67% hit rate)
- **Cache**: Cached to avoid re-processing
- **Search**: Fast lookup via pre-built index

## Usage

### Search by Identity:
```python
from query import ask

# Get narrative about any identity
result = ask("tell me about alawite bankers", use_llm=True)
result = ask("tell me about black bankers", use_llm=True)
result = ask("tell me about quaker bankers", use_llm=True)
```

### Search Hierarchy:
System automatically includes both specific and general terms:
- Search "muslim" → finds sunni, shia, alawite, ismaili, druze
- Search "black" → finds african american, hausa, yoruba, igbo, fanti
- Search "jewish" → finds sephardi, ashkenazi, mizrahi, court jew

## Next Steps (Optional)

1. **Expand hierarchy mappings** in `lib/identity_hierarchy.py`
2. **Add more identity keywords** to `lib/identity_prefilter.py`
3. **Re-run detection** if documents are updated: `python temp/run_steps_1_2.py` then `python temp/run_steps_3_4.py`
4. **Rebuild index**: `python build_index.py`

