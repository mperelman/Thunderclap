# Proposal: Dynamic Cousinhood Detection

## Current State (Hardcoded)
- `lib/cousinhoods.py`: 60+ hardcoded family names across 13 cousinhoods
- Must manually maintain when adding new families
- Risk of missing families in documents

## Opportunity (Documents Have the Data!)

### Evidence Found:
1. **719 matches** of identity+family patterns ("Quaker Barclay", "Jewish Rothschild")
2. **Explicit cousinhood mentions**: "renewed relations with the cousinhood"
3. **Entity associations**: `rothschild` → `warburg`, `oppenheim`, `goldschmidt`
4. **Marriage patterns**: "Sedgwicks thoroughly intermarried with Russells, Cabots, Channings, Peabodys"

## Proposed Approach: Learn from Documents

### Phase 1: Extract Identity-Family Pairs
```python
# Parse documents for patterns:
# - "Quaker Barclay" → (quaker, barclay)
# - "Jewish Rothschild" → (jewish, rothschild)
# - "Boston Brahmin Cabot" → (boston brahmin, cabot)

def extract_identity_family_pairs(chunks):
    patterns = [
        r'(quaker|jewish|huguenot|parsee|hindu|brahmin|etc)\s+([A-Z][a-z]+)',
        r'([A-Z][a-z]+)\s+(quaker|jewish|huguenot|etc)'
    ]
    # Returns: {identity: [families]}
```

### Phase 2: Build Cousinhoods from Co-occurrence
```python
# Use entity_associations to find which families co-occur
# Example: rothschild co-occurs with warburg, oppenheim
# + both are labeled "jewish" in documents
# = Jewish cousinhood

def build_cousinhoods_from_associations(identity_families, entity_associations):
    cousinhoods = {}
    for identity, families in identity_families.items():
        # Get families that (1) share identity AND (2) co-occur frequently
        cousinhood_members = cluster_by_cooccurrence(families, entity_associations)
        cousinhoods[identity] = cousinhood_members
    return cousinhoods
```

### Phase 3: Detect Geographic Clusters
```python
# Documents say: "Barclay... Lloyd... Britain"
# Documents say: "Hope... Amsterdam", "Mallet... Britain"
# = Huguenot cousinhood split by geography

def detect_geographic_clusters(cousinhoods, chunks):
    for identity, families in cousinhoods.items():
        # Find what geographies are mentioned with these families
        geographic_clusters = group_by_geography(families, chunks)
        # Example: Huguenot -> {amsterdam: [Hope], britain: [Mallet, Thellusson]}
```

### Phase 4: Validate Against Known Patterns
```python
# Use current lib/cousinhoods.py as VALIDATION
# Check: Did we find Barclay, Lloyd, Bevan in Quaker cluster?
# Check: Did we find Rothschild, Warburg in Jewish cluster?
# Report: Coverage % vs hardcoded list
```

## Implementation Plan

### Step 1: Build Cousinhood Detector (NEW MODULE)
```python
# lib/cousinhood_detector.py
class CousinoodDetector:
    def extract_from_documents(self, documents):
        # Phase 1-3 above
        return {
            'cousinhoods': {...},
            'confidence': 0.85,
            'coverage': '92% of hardcoded list found'
        }
```

### Step 2: Integrate into Index Builder
```python
# lib/index_builder.py
def build_indices(...):
    # Existing code
    
    # NEW: Detect cousinhoods from documents
    detected_cousinhoods = detect_cousinhoods(chunks, entity_associations)
    
    # Save for query-time use
    return {
        'term_to_chunks': ...,
        'entity_associations': ...,
        'detected_cousinhoods': detected_cousinhoods  # NEW
    }
```

### Step 3: Hybrid Approach (Fallback)
```python
# lib/cousinhoods.py becomes FALLBACK
# - If detection confidence > 80% → use detected
# - Else → fallback to hardcoded
# - Log differences for review
```

## Benefits

### 1. **Auto-Discovery**
- System learns new families from documents automatically
- Example: If documents mention "Mennonite Fock" 50 times, system adds Fock to Mennonite cousinhood

### 2. **Data-Driven Confidence**
- Cousinhood membership based on document evidence, not manual curation
- Can report: "Barclay mentioned as Quaker in 127 chunks"

### 3. **Reduced Maintenance**
- Add new document → system learns new families
- No manual updating of hardcoded lists

### 4. **Geographic Precision**
- Automatically clusters by geography from document context
- Example: "Hope appeared with Amsterdam in 45 chunks, with Britain in 12 chunks"

### 5. **Kinlink Detection**
- Automatically find cross-group patterns
- Example: "Oppenheim co-occurs with Stein 23 times" → kinlink detected

## Challenges

### 1. **Ambiguity**
- "Brahmin" = Hindu caste OR Boston Brahmin
- Need context to distinguish

### 2. **Coverage**
- Some families rarely mentioned might not be detected
- Hardcoded list provides baseline

### 3. **Validation**
- Need to verify detected cousinhoods make sense
- Use current hardcoded list as ground truth

## Next Steps

**Want me to implement this?**

1. Create `lib/cousinhood_detector.py` module
2. Extract identity-family pairs from documents
3. Build cousinhoods from co-occurrence + identity
4. Validate against current hardcoded list
5. Report: What % can be auto-detected?

This would transform the system from **manually curated** to **data-driven**!

