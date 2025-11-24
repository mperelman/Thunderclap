# LGBT & Latino Detection Approach

## Key Decision: Context vs Individuals

### LGBT: Context-Based (NOT Individual Tagging)

**Approach:** Use keyword search only, don't tag individuals

**Why:**
- LGBT is about **historical context**: lavender marriages, AIDS crisis, homophobia, legal changes
- Names appear in LGBT AND non-LGBT contexts (Drexel mentioned 100+ times, mostly NOT about LGBT)
- Tagging "Drexel" as LGBT would make ALL Drexel chunks appear for "gay bankers" ❌
- Want ONLY chunks discussing LGBT topics ✓

**How It Works:**
```
Search: "gay bankers" or "lgbt bankers"
    ↓
Keyword search finds chunks with:
  - "gay", "lgbt", "lesbian", "bisexual"
  - "homosexual", "homosexuality"
  - "lavender" (marriages)
  - "aids" (crisis)
  - "openly gay", "closeted", etc.
    ↓
Returns chunks about:
  ✓ Lavender marriages (mentions Drexel, Singer, Barney IN CONTEXT)
  ✓ AIDS crisis (mentions specific individuals IN CONTEXT)
  ✓ Homophobia and discrimination
  ✓ Legal changes (decriminalization, marriage equality)
  ✓ Coming out stories
  ✓ General LGBT banking culture
```

**Result:** Comprehensive LGBT context for narrative, without tagging individuals incorrectly

**Prevents:**
- ❌ "Claudine Gay" (Harvard president, surname is "Gay" - not LGBT)
- ❌ ALL Drexel chunks (only want the lavender marriages chunk)

### Latino: Individual-Based (Extract Specific People)

**Approach:** Detect Latino/Hispanic individuals, tag them

**Why:**
- Latino is about **specific people's ethnicity**: Aida Alvarez, Roberto Goizueta
- Unlike LGBT, ethnicity follows individuals across ALL contexts
- Want ALL chunks about Alvarez when searching "latino bankers" ✓

**How It Works:**
```
Detector finds:
  - "Puerto Rican Aida Alvarez"
  - "first Latina... Alvarez"
  - Covers ALL Latin American countries
    ↓
Tags: alvarez, goizueta, salinas as "latino"
    ↓
Search: "latino bankers"
    ↓
Finds:
  ✓ Chunks with "latino", "hispanic", "puerto rican" keywords
  ✓ ALL chunks about Alvarez (even if no mention of ethnicity)
  ✓ ALL chunks about Goizueta (even if no mention of ethnicity)
```

**Result:** Find specific Latino bankers across their full careers

## Summary

| Identity | Approach | Reason |
|----------|----------|--------|
| **LGBT** | Keyword search only | Context-based, not hereditary |
| **Latino** | Individual tagging | Ethnic identity across all contexts |
| **Black** | Individual tagging | Racial identity across all contexts |
| **Jewish** | Family tagging | Hereditary (all Rothschilds are Jewish) |
| **Quaker** | Family tagging | Hereditary (all Barclays are Quaker) |
| **Female** | Individual tagging | Gender identity (widow merged in) |

## Implementation

### LGBT (Keyword Search)
- No extraction in `identity_detector.py`
- Relies on existing keyword index
- Terms: gay, lgbt, lesbian, bisexual, homosexual, lavender, aids
- "gay" added to noise_words (prevents "Claudine Gay" false positive)

### Latino (Individual Tagging)
- Patterns in `identity_detector.py`
- Covers ALL Latin American countries (Honduras, Colombia, Venezuela, etc.)
- Detects: alvarez, goizueta, salinas
- All chunks about these individuals tagged for "latino bankers" search

## Next Step

**Rebuild index** to include latest terms:
```bash
python build_index.py
```

This will:
1. Reindex ALL terms (including "lavender", "bisexual", etc.)
2. Run identity detector (finds Latino individuals)
3. Augment index (links Latino individuals to search)
4. Enable comprehensive LGBT keyword search + Latino individual search


