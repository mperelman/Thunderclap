# LLM Detector - What It Asks & What Failed

## What the LLM Detector Asks For

The detector sends chunks of text to the LLM with this task:

**PROMPT:**
```
You are a banking historian extracting identity attributes from text.

TASK: For EACH surname mentioned, list ALL identity attributes explicitly stated.

IDENTITY CATEGORIES - Extract the MOST SPECIFIC term:

Religion (BE SPECIFIC):
- Muslim: sunni, shia, alawite, ismaili, druze
- Christian: maronite, coptic, greek_orthodox, protestant, quaker, huguenot
- Jewish: sephardi, ashkenazi, court_jew, kohanim
- Other: hindu, parsee, zoroastrian

Ethnicity (BE SPECIFIC):
- Levantine: lebanese, syrian, palestinian
- African: hausa, yoruba, igbo (NOT generic 'african')
- European: basque, scottish, irish, welsh
- Latin American: mexican, cuban, puerto_rican, hispanic, latino

Race: black, white (only if explicit)

Gender: female, queen, princess, widow

RULES:
1. Extract ALL explicitly stated attributes
2. Multi-generational: "converted Jewish Hambro" → ["jewish", "converted", "christian"]
3. Return SPECIFIC terms (sunni NOT muslim, maronite NOT christian)

EXAMPLES:
- "Jewish Rothschild" → {"rothschild": ["jewish"]}
- "Sephardi Chavez, mother of Basque descent" → {"chavez": ["sephardi", "basque"]}

---

**CHUNK 1:**
[Full text of chunk here - 500 words]

**CHUNK 2:**
[Full text of chunk here - 500 words]

---

ANSWER (JSON format):
{
  "chunk_1": {"rothschild": ["jewish"], "barclay": ["quaker"]},
  "chunk_2": {"sassoon": ["sephardi"], "tata": ["parsee"]}
}
```

---

## Why It Failed Before (99.7% Failure Rate)

### THE BROKEN LOGIC (v1):

**Step 1: Pre-extraction (BROKEN)**
```python
# If chunk contained word "jewish" ANYWHERE:
if 'jewish' in chunk:
    # Extract ALL proper names in ENTIRE chunk:
    surnames = find_all_proper_names(chunk)  # Could be 50+ names
    candidates['jewish'] = surnames  # ALL 50!
```

**Step 2: Send to LLM**
```
**CHUNK 1:**
[500 word chunk about banking in 1800s London]

SURNAMES: Rothschild, Baring, Hope, Morgan, Brown, Smith, Johnson, 
Williams, Jones, Davis, Miller, Wilson, Anderson, Taylor, Thomas,
Jackson, White, Harris, Martin, Thompson, Garcia, Martinez, Robinson,
Clark, Lewis, Lee, Walker, Hall, Allen, Young, King, Wright, Lopez,
Hill, Scott, Green, Adams, Baker, Gonzalez, Nelson, Carter, Mitchell,
Perez, Roberts, Turner...

[50+ surnames because chunk mentioned "jewish" once!]
```

**Result:**
- LLM sees 50+ surnames
- Only 1-2 are actually Jewish
- LLM says: "I can't tell which are Jewish from this list"
- Returns: `{}`  (empty)
- **99.7% failure rate**

---

## What Changed (v2 - FIXED)

### THE NEW LOGIC (Simplified):

**Step 1: Check if chunk has identity keywords**
```python
# Just check if chunk has ANY identity keyword
if any(keyword in chunk for keyword in ['jewish', 'black', 'lebanese', ...]):
    send_to_llm = True  # Worth processing
```

**Step 2: Send FULL CHUNK to LLM (NO pre-extraction)**
```
**CHUNK 1:**
[FULL 500 word chunk]

Jewish Rothschild merged with Quaker Barclay in London.
The Sephardi Sassoon family traded with Parsee Tata in India.
Black banker Richard Parsons joined Citi in New York.
Lebanese Maronite George Boutros worked at CSFB.
[... rest of chunk ...]
```

**LLM Response:**
```json
{
  "chunk_1": {
    "rothschild": ["jewish"],
    "barclay": ["quaker"],
    "sassoon": ["sephardi"],
    "tata": ["parsee"],
    "parsons": ["black"],
    "boutros": ["lebanese", "maronite"]
  }
}
```

**Result:**
- LLM sees full context
- Can identify which surnames have which identities
- Should detect 100s of identities, not just 8

---

## Comparison

### Before (v1 - Broken):
```
Chunk: "Jewish Rothschild and Quaker Barclay traded in London..."

Pre-extraction: 
  jewish → [Rothschild, Barclay, London, Bank, Smith, Jones, ...]

LLM receives: "Which of these 50 surnames are Jewish?"
LLM returns: {} (confused)
```

### After (v2 - Fixed):
```
Chunk: "Jewish Rothschild and Quaker Barclay traded in London..."

No pre-extraction!

LLM receives: [Full chunk text]
LLM returns: {"rothschild": ["jewish"], "barclay": ["quaker"]}
```

---

## Why This Fix Works

**Old approach:**
- Tried to be "smart" by pre-extracting surnames
- Extracted WRONG surnames (all of them if keyword appeared)
- Sent garbage to LLM
- LLM couldn't figure it out

**New approach:**
- Trust the LLM to do ALL the work
- Send full context
- LLM is much smarter than my regex
- Should work properly

---

## Testing at 3am

**Run:** `python temp/run_at_3am.py`

This will:
1. Test API key (1 request)
2. Test on 5 chunks (~1 request)
3. Show you results
4. Ask before running full 1,516 chunks (~75 requests)

**Expected:**
- Should detect dozens of identities from just 5 chunks
- Proof it's working before full run
- Won't waste quota if still broken


